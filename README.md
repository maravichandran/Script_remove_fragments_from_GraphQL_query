# Script to defragmentify (remove fragments from) GraphQL query
 Python script to remove all fragments (including nested fragments) from a GraphQL query and replace them with the fragment bodies.

This script removes fragments from a GraphQL query by replacing all references to fragments with the fragments' bodies, and then deleting the now-unused fragment bodies from the file.

Example usage from terminal:
```bash
python remove_fragments_from_graphql_query.py input_file.graphql output_file.graphql
```

The resulting query does not retain pretty formatting, but you can auto-format it with Prettier.

(Add the `-d` flag (short for `--delete_typename`) to the commmand if you want to delete
all occurrences of `__typename` from the file as well. You usually wouldn't want to
do this as `__typename` is required for Apollo GraphQL queries, but I had added
this functionality for something specific I wanted to do.)
