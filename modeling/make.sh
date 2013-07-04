#/bin/bash
set -e

function failure() {
  echo "💣 SOMETHING WENT WRONG💣 "
}
trap failure 0

function success() {
  echo "🍻 Success"
}

echo "✨ HEY, LISTEN!✨ "
echo "This script assumes that you've already manually exported rod_endpoints.txt from Rhino"
echo "You can do that in Rhino by selecting Tools > Command > Search..."
echo "and typing RunPythonScript"
echo "when the first file open dialog box appears, use it to select exportRodEndpoints.py"
echo "when the second file open dialog box appears, use it to select rod_endpoints.txt for overwriting"

echo
echo "🔥 Converting rod_endpoints.txt to graph.data.json"
./figure_out_graph.py rod_endpoints.txt > graph.data.json

echo "💡 Converting graph.data.json to opc-layout.json"
./graph_to_layout.py graph.data.json opc-layout.json

if type dot 2>/dev/null > /dev/null ; then
echo "🌐 Converting graph.data.json to graph.png"
  ./graphvizify.py graph.data.json > graph.dot
  dot -T png -o graph.png graph.dot
  neato -T png -o graph2.png graph.dot
else
  echo "HEY: install graphvis to produce graph.png"
fi

#echo "🎄 Converting graph.data.json to rod_addresses.json"
#./map_rods_to_addresses.py graph.data.json > rod_addresses.json

echo "🎄 Converting graph.data.json to rod_addresses.json"
./assign_rod_addresses.py graph.data.json > rod_addresses.json

trap success 0
