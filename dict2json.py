# no indent
from collections import defaultdict, OrderedDict
import json

video = defaultdict(list)
video["label"].append("haha")
video["data"].append(234)
video["score"].append(0.3)
video["label"].append("xixi")
video["data"].append(123)
video["score"].append(0.7)

test_dict = {
    'version': "1.0",
    'results': video,
    'explain': {
        'used': True,
        'details': "this is for josn test",
  }
}

json_str = json.dumps(test_dict)
with open('test_data.json', 'w') as json_file:
    json_file.write(json_str)



# indent
from collections import defaultdict, OrderedDict
import json

video = defaultdict(list)
video["label"].append("haha")
video["data"].append(234)
video["score"].append(0.3)
video["label"].append("xixi")
video["data"].append(123)
video["score"].append(0.7)

test_dict = {
    'version': "1.0",
    'results': video,
    'explain': {
        'used': True,
        'details': "this is for josn test",
  }
}

json_str = json.dumps(test_dict, indent=4)
with open('test_data.json', 'w') as json_file:
    json_file.write(json_str)