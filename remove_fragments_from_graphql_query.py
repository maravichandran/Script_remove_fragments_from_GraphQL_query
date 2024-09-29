"""
This script removes fragments from a GraphQL query by replacing all
references to fragments with the fragments' bodies, and then deleting
the now-unused fragment bodies from the file.

Example usage from terminal:
python remove_fragments_from_graphql_query.py input_file.graphql output_file.graphql

The resulting query does not retain pretty formatting, but you can auto-format it with Prettier.

(Add the -d flag (short for --delete_typename) if you want to delete
all occurrences of '__typename' from the file as well. You usually wouldn't want to
do this as __typename is required for Apollo GraphQL queries, but I had added
this functionality for something specific I wanted to do.)
"""

import re
import argparse
from typing import List, Dict
from collections import namedtuple

FragmentInfo = namedtuple(
    "Fragment_Info", ["start_index", "body_start_index", "end_index", "is_typecast"]
)


def _find_fragment_names(query: str) -> List[str]:
    """Returns a list of names of fragments in the query."""
    fragment_def_regex = r"(?<=fragment )[A-Za-z0-9]+(?= on)"
    fragment_names = re.findall(fragment_def_regex, query)
    return fragment_names


def _get_fragment_and_body_indices(fragment_name: str, query: str) -> FragmentInfo:
    """
    Returns the start index, start of the body index, and end index of the fragment with the given name.

    To account for typecasting, if the 'on' keyword is present, the body start
    index of a fragment is at the beginning of the 'on' keyword, and the
    end index is one after the closing curly brace, so that it's included in
    list slicing.

    If the 'on' keyword is not present, the body start index is defined as the
    first character inside the curly braces of the fragment, and the end
    index is the index of the fragment's closing curly brace.
    """
    start_index = query.find("fragment {}".format(fragment_name))
    curly_brace_count = 1
    body_start_index = query.find("{", start_index) + 1
    for i in range(body_start_index, len(query)):
        if query[i] == "{":
            curly_brace_count += 1
        elif query[i] == "}":
            curly_brace_count -= 1
        if curly_brace_count == 0:
            end_index = i
            break
    is_typecast = False
    # "on" must be its own word rather than part of another var,
    # hence the spaces around it in the search
    search_result = query.find(" on ", start_index, body_start_index)
    if search_result != -1:
        # add 1 to body_start_index since it should start at the letter "o" in "on"
        body_start_index = search_result + 1
        end_index += 1
        is_typecast = True
    fragment_indices = FragmentInfo(
        start_index, body_start_index, end_index, is_typecast
    )
    return fragment_indices


def _get_fragment_body(fragment_name: str, query: str) -> str:
    """Returns the body of the fragment with the given name."""
    fragment_info = _get_fragment_and_body_indices(fragment_name, query)
    fragment_body = query[fragment_info.body_start_index : fragment_info.end_index]
    if fragment_info.is_typecast:
        fragment_body = "... " + fragment_body
    return fragment_body


def _create_fragment_mapping(query: str) -> Dict[str, str]:
    """Returns a mapping of fragment names to fragment bodies."""
    fragment_names = _find_fragment_names(query)
    fragment_mapping = {}
    for curr_fragment_name in fragment_names:
        fragment_body = _get_fragment_body(curr_fragment_name, query)
        fragment_mapping[curr_fragment_name] = fragment_body
    return fragment_mapping


def _remove_fragment_definitions(query: str, fragment_mapping: Dict[str, str]) -> str:
    """Returns a query with all fragment definitions removed."""
    for fragment_name in fragment_mapping.keys():
        fragment_info = _get_fragment_and_body_indices(fragment_name, query)
        query = (
            query[: fragment_info.start_index] + query[fragment_info.end_index + 1 :]
        )
    return query


def _replace_fragment_references_with_fragment_bodies(
    query: str, fragment_mapping: Dict[str, str]
) -> str:
    """Returns a query with all fragment name references replaced with the fragment body."""
    for name, body in fragment_mapping.items():
        fragment_references_regex = r"\.\.\.{}\b".format(name)
        query = re.sub(fragment_references_regex, body, query)
    return query


def _replace_all_fragment_references(
    query: str, fragment_mapping: Dict[str, str]
) -> str:
    """
    Iterates through the query and replaces fragment references with their bodies until
    no more fragment references remain. This allows for the handling of nested fragments.
    """
    while True:
        fragment_references = re.findall(r"\.\.\.[A-Za-z]+", query)
        print("# remaining fragment references:", len(fragment_references))
        if not fragment_references:
            break
        query = _replace_fragment_references_with_fragment_bodies(
            query, fragment_mapping
        )
    return query


def remove_empty_lines(string: str) -> str:
    """Returns a string with extra blank lines removed."""
    return re.sub(r"\n\s*\n", "\n", string)


def remove_fragments_from_query(file_path: str) -> str:
    """Removes all fragments from the inputted GraphQL query file and outputs the result as a string."""
    with open(file_path, "r") as file:
        query = file.read()

    fragment_mapping = _create_fragment_mapping(query)

    query_no_unused_fragments = _remove_fragment_definitions(query, fragment_mapping)
    query_no_unused_fragments = remove_empty_lines(query_no_unused_fragments)

    query_no_fragment_refs = _replace_all_fragment_references(
        query_no_unused_fragments, fragment_mapping
    )
    query_no_fragment_refs = remove_empty_lines(query_no_fragment_refs)

    return query_no_fragment_refs.strip()


def main(
    input_file_path: str, output_file_path: str, delete_typename: bool = False
) -> None:
    modified_query = remove_fragments_from_query(input_file_path)

    if delete_typename:
        print("Deleting occurrences of '__typename' from file.")
        modified_query = modified_query.replace("__typename\n", "")

    with open(output_file_path, "w") as file:
        file.write(modified_query)

    print(f"Modified query written to {output_file_path}")


if __name__ == "__main__":
    # parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file_path", help="Input GraphQL file")
    parser.add_argument("output_file_path", help="Output GraphQL file")
    parser.add_argument(
        "-d",
        "--delete_typename",
        help="Set to True if you'd like to delete occurrences of __typename",
        default=False,
        action="store_true",
    )
    args = parser.parse_args()

    # Call the main function with parsed arguments
    main(args.input_file_path, args.output_file_path, args.delete_typename)
