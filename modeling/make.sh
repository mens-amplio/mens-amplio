#/bin/bash
set -e
echo "✨ HEY, LISTEN!✨ "
echo "This script assumes that you've already manually exported rod_endpoints.txt from Rhino"
echo "You can do that in Rhino by selecting Tools > Command > Search..."
echo "and typing RunPythonScript"
echo "when the first file open dialog box appears, use it to select exportRodEndpoints.py"
echo "when the second file open dialog box appears, use it to select rod_endpoints.txt for overwriting"

echo
echo "Converting rod_endpoints.txt to graph.data.json"
./figure_out_graph.py rod_endpoints.txt > graph.data.json

echo "Converting graph.data.json to opc-layout.json"
./graph_to_layout.py graph.data.json opc-layout.json
