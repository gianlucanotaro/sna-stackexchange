from stackapi import StackAPI
import time
import json

#
# ----------------------------------------------------------------------
# WORK IN PROGRESS
# ----------------------------------------------------------------------
#

# import importlib
# importlib.reload(sna)

class CsvOutput():

	def __init__(self):
		# [sourceid, targetid, type, id, label, interval, weight]
		self.edges = []
		# {label : id}
		self.nodes = {}

	def add_data_row(self, source_label, target_label, type='Unidirected', label='', interval='', weight=1) -> None:
		if source_label not in self.nodes.keys(): self.nodes[source_label] = len(self.nodes)
		if target_label not in self.nodes.keys(): self.nodes[target_label] = len(self.nodes)
		id = len(self.edges)
		source_id = self.nodes[source_label]
		target_id = self.nodes[target_label]
		self.edges.append([source_id, target_id, type, id, label, interval, weight])

	def _csv_formatted_edges(self) -> str:
		return 'Source, Target,Type,Id,Label,timeset,Weight\n'+'\n'.join([','.join([str(i) for i in line]) for line in self.edges])

	def _csv_formatted_nodes(self) -> str:
		return 'Id,Label,timeset\n'+'\n'.join([str(id)+','+label+',' for label, id in self.nodes.items()])

	def export_to_csv(self, edge_file_name: str = 'edge_export.csv', node_file_name: str = 'node_export.csv') -> None:
		with open(edge_file_name, 'w') as f:
			f.write(self._csv_formatted_edges())
		with open(node_file_name, 'w') as f:
			f.write(self._csv_formatted_nodes())

class Graph:

	def __init__(self):
		# {source: {target: weight, ... }}
		# source - weight -> target
		self.graph = dict()

	def add_edge(self, node_a: str, node_b: str, weight: int=1, unidirected: bool = True) -> None:
		if(node_a not in self.graph.keys()): self.graph[node_a] = {node_b: weight}
		elif(node_b not in self.graph[node_a].keys()): self.graph[node_a][node_b] = weight
		else: self.graph[node_a][node_b] += weight

	def to_csvOutput(self) -> CsvOutput:
		csvOutput = CsvOutput()
		for source, i in self.graph.items():
			for target, weight in i.items():
				csvOutput.add_data_row(source_label=source, target_label=target, weight=weight)
		return csvOutput

class UniqueQuestions:

	def __init__(self):
		self._data = {}

	def __len__(self) -> int:
		return len(self._data)

	def extend(self, questions: list) -> None:
		prev = len(self._data)
		for question in questions:
			self._data[question['question_id']] = question
		post = len(self._data)
		print('new questions:', (post-prev))

	# ------------------------------------------------------------------
	# implement graph conversion here
	# ------------------------------------------------------------------
	def graph_from_tags(self) -> Graph:
		graph = Graph()
		
		for _, question in self._data.items():
			for tag_a in question['tags']:
				for tag_b in question['tags']:
					if tag_a < tag_b:
						graph.add_edge(tag_a, tag_b)
		return graph

	def graph_from_xyz(self) -> Graph:
		"""
		example
		"""
		graph = Graph()
		return graph()
	# ------------------------------------------------------------------
	# implement graph conversion here
	# ------------------------------------------------------------------



class StackFetcher:


	def __init__(self):
		self._questions = UniqueQuestions()

	def fetch(self, stack_api: StackAPI, iterations: int = 1, time_delta: int = 3600) -> int:
		ts = int(time.time())
		for i in range(iterations):
			response = stack_api.fetch('questions', fromdate=ts-(i+1)*time_delta, todate=ts-i*time_delta)
			self._questions.extend(response['items'])
			print('number of total questions: ', len(self._questions))
			print(i+1, '/', iterations)
			time.sleep(1)
		print('quota_remaining:', response['quota_remaining'])

	def json_dump_questions(self, file_name: str) -> None:
		print('number of dumped questions:', len(self._questions))
		with open(file_name, 'w') as f:
			f.write(json.dumps(list(self._questions._data.values())))

	def json_load_questions(self, file_name: str) -> None:
		with open(file_name, 'r') as f:
			# json does not support integers as dictionary keys
			loaded_questions = json.loads(f.read())
			self._questions.extend(loaded_questions)
			print('number of loaded questions:', len(loaded_questions))

	def get_uniqueQuestions(self) -> UniqueQuestions:
		return self._questions

#
# ----------------------------------------------------------------------
#
if __name__ == '__main__':

	stack_api = StackAPI('stackoverflow')

	sf = StackFetcher()

	sf.json_load_questions()
	sf.fetch(stack_api, iterations=1, time_delta=7200)
	sf.json_dump_questions()

	uq = sf.get_uniqueQuestions()
	graph = uq.graph_from_tags()
	csv_output = graph.to_csvOutput()

	csv_output.export_to_csv()
