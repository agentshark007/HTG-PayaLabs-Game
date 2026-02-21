echo "-----Formatting-----"
echo "-----autopep8"
autopep8 --recursive --aggressive --in-place .
echo "-----isort-----"
isort .
echo "-----black-----"
black .
echo "-----restore pgiud-----"
git restore pgiud.py
echo "-----Done formatting-----"
