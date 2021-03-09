import pprint, pickle

# pkl_file = open('deeprm/data/pg_re_2.pkl', 'rb')
# /home/dev/project_Deeprm/deeprmCode/deeprmCode/deeprm/data/pg_re_2.pkl
pkl_file = open('data/pg_re_2.pkl', 'rb')

data1 = pickle.load(pkl_file)
pprint.pprint(data1)

# data2 = pickle.load(pkl_file)
# pprint.pprint(data2)

pkl_file.close()
