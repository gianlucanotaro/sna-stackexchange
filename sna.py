from stackapi import StackAPI
import time
import datetime
import numpy as np
import matplotlib.pyplot as plt
from datetime import time as t
import json

#
# ----------------------------------------------------------------------
# WORK IN PROGRESS
# ----------------------------------------------------------------------
#

# import importlib
# importlib.reload(sna)

#
# satisfy typechecker because of circular references
#
class UniqueQuestions:
	pass

class StackFetcher:
	pass

class CsvOutput():
	pass


#
#
#
	

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

	def export_to_csv(self, edge_file_name: str, node_file_name: str) -> None:
		with open(edge_file_name, 'w') as f:
			f.write(self._csv_formatted_edges())
		print('created:', edge_file_name)
		with open(node_file_name, 'w') as f:
			f.write(self._csv_formatted_nodes())
		print('created:', node_file_name)

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
		return sum([len(d.keys()) for _, d in self._data.items()])

	def as_json(self) -> str:
		return json.dumps({stack_name: {str(id): values for id, values in questions.items()} for stack_name, questions in self._data.items()})

	@classmethod
	def from_json(cls, json_string: str) -> UniqueQuestions:
		uq = UniqueQuestions()
		loaded_q = json.loads(json_string)
		uq._data = {stack_name: {int(id): question for id, question in questions.items()} for stack_name, questions in loaded_q.items()}
		return uq

	def extend(self, stack_name: str, questions: list) -> None:
		if stack_name not in self._data.keys(): self._data[stack_name] = {}
		for question in questions:
			self._data[stack_name][question['question_id']] = question

	# ------------------------------------------------------------------
	# implement graph conversion here
	# ------------------------------------------------------------------
	def graph_from_tags(self) -> Graph:
		graph = Graph()
		for _, stacks in self._data.items():
			for _, question in stacks.items():
				for tag_a in question['tags']:
					for tag_b in question['tags']:
						if tag_a < tag_b:
							graph.add_edge(tag_a, tag_b)
		return graph

	def graph_from_timezones(self) -> Graph:
		graph = Graph()
		# TIMEZONES: USSA: 0-=<8, EUAF:>8-<=16, ASAU:>16-<=23:59
		for _, stacks in self._data.items():
			for _, question in stacks.items():
				tags = question['tags']
				questionTime = datetime.datetime.fromtimestamp(question['creation_date'])
				for tag in tags:
					if questionTime.time() <= t(hour = 8, minute = 0, second = 0):
						graph.add_edge('USSA', tag)
					elif questionTime.time() > t(hour = 8, minute = 0, second = 0) and questionTime.time() <= t(hour = 16, minute = 0, second = 0):
						graph.add_edge('EUAF', tag)
					else:
						graph.add_edge('ASAU', tag)
		return graph

	def graph_from_stacks(self) -> Graph:
		graph = Graph()
		for stack, questions in self._data.items():
			for _, question in questions.items():
				graph.add_edge(str(stack), question['owner']['display_name'])
		return graph

	def graph_from_rating(self) -> Graph:
		graph = Graph()
		ratings = []
		for stack, questions in self._data.items():
			for _, question in questions.items():
				ratings.append(question['score'])
		print(ratings)
		a = np.mean(ratings)
		b = np.std(ratings)
		print(a)
		print(b)
		plt.hist(ratings)
		plt.show()
		return graph

	# ------------------------------------------------------------------
	# implement graph conversion here
	# ------------------------------------------------------------------


class StackFetcher:

	def __init__(self):
		self._questions = UniqueQuestions()

	def fetch(self, stack_apis: [StackAPI], iterations: int = 1, time_intvl: int = 3600, time_diff: int = 0) -> int:
		ts = int(time.time())
		for stack_api in stack_apis:
			for i in range(iterations):
				response = stack_api.fetch('questions', fromdate=ts-(i+1)*time_intvl-time_diff, todate=ts-i*time_intvl-time_diff)
				self._questions.extend(stack_api._name, response['items'])
				print('number of total questions: ', len(self._questions))
				print(i+1, '/', iterations)
				time.sleep(1)
			print('quota_remaining:', response['quota_remaining'])

	def json_dump_questions(self, file_name: str) -> None:
		print('number of dumped questions:', len(self._questions))
		with open(file_name, 'w') as f:
			f.write(self._questions.as_json())

	def json_load_questions(self, file_name: str) -> None:
		with open(file_name, 'r') as f:
			self._questions = UniqueQuestions.from_json(f.read())
			print('number of loaded questions:', len(self._questions))
			
	def get_uniqueQuestions(self) -> UniqueQuestions:
		return self._questions
#
# ----------------------------------------------------------------------
#
def main():
	stack_api = [StackAPI('stackoverflow'),StackAPI('math')]

	sf = StackFetcher()

	#sf.json_load_questions('qs.json')
	sf.fetch(stack_api, iterations=1, time_intvl=3600, time_diff=3600*24*7)
	sf.json_dump_questions('qs.json')

	uq = sf.get_uniqueQuestions()

	graph_tags = uq.graph_from_tags()
	graph_timezones = uq.graph_from_timezones()
	graph_stacks = uq.graph_from_stacks()
	graph_rating = uq.graph_from_rating()

	csv_tag_output = graph_tags.to_csvOutput()
	csv_timezone_output = graph_timezones.to_csvOutput()
	csv_stack_output = graph_stacks.to_csvOutput()
	csv_rating_output = graph_rating.to_csvOutput()
	
	csv_tag_output.export_to_csv('edge_tag.csv', 'node_tag.csv')
	csv_timezone_output.export_to_csv('edge_timezone.csv', 'node_timezone.csv')
	csv_stack_output.export_to_csv('edge_stack.csv', 'node_stack.csv')
	#csv_rating_output.export_to_csv('edge_rating.csv', 'node_rating.csv')
	
if __name__ == '__main__':
	main()
