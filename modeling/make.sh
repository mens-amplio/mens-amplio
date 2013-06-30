set -e
echo "✨ HEY, LISTEN!✨ "
echo "This script assumes that you've already manually exported curve_endpoints.txt from Rhino"
echo "You can do that in Rhino by selecting Tools > Command > Search..."
echo "and typing RunPythonScript"
echo "when the first file open dialog box appears, use it to select exportCylinderEndpoints.py"
echo "when the second file open dialog box appears, use it to select curve_endpoints.txt for overwriting"

echo
echo "Converting curve_endpoints.txt to graph.data.json"
python figure_out_graph.py > graph.data.json

echo "TODO, whatever happens next, hang on I'm shaving a yak"
