import _pickle as cpickle
import os

current_path = os.getcwd()
parent_path = os.path.dirname(current_path)

pickle_path = os.path.join(parent_path, 'Data', 'mc_analysis', 'test_output.p')
test_output = cpickle.load(open(pickle_path, 'rb'))