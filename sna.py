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
		with open(edge_file_name, 'w', encoding='utf-8') as f:
			f.write(self._csv_formatted_edges())
		print('created:', edge_file_name, 'edges:', len(self.edges))
		with open(node_file_name, 'w', encoding='utf-8') as f:
			f.write(self._csv_formatted_nodes())
		print('created:', node_file_name, 'nodes:', len(self.nodes))

class Graph:

	def __init__(self):
		# {source: {target: weight, ... }}
		# source - weight -> target
		self.graph = dict()

	def add_edge(self, node_a: str, node_b: str, weight: int=1, unidirected: bool = True) -> None:
		if(node_a not in self.graph.keys()): self.graph[node_a] = {node_b: weight}
		elif(node_b not in self.graph[node_a]): self.graph[node_a][node_b] = weight
		else: self.graph[node_a][node_b] += weight

	def to_csvOutput(self) -> CsvOutput:
		csvOutput = CsvOutput()
		for source, i in self.graph.items():
			for target, weight in i.items():
				csvOutput.add_data_row(source_label=source, target_label=target, weight=weight)
		return csvOutput

	def filter_min_occurences(self, occurences : int) -> None:
		graph = dict()
		for node,subnode in self.graph.items():
			for tag,value in subnode.items():
				if value >= occurences:
					if node not in graph:
						graph[node] = dict()
					graph[node][tag] = value
		self.graph = graph

	def filter_min_different_destinations(self, diff_dest) -> None:
		graph = dict()
		for src, edge in self.graph.items():
			if len(edge) >= diff_dest:
				graph[src] = {}
				for dst, weight in edge.items():
					graph[src][dst] = weight
		self.graph = graph
		
class UniqueQuestions:

	def __init__(self):
		self._data = {}

	def __len__(self) -> int:
		return sum([len(d.keys()) for _, d in self._data.items()])
		
	def __str__(self) -> str:
		return 'no questions:' + str(self.__len__()) + '\n' +\
				'-'*40 +'\n' +\
				'\n'.join([k + ': ' + str(len(v)) for k, v in self._data.items()]) + '\n' + \
				'-'*40\

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

	def graph_from_timezones_normalized_filtered(self, min_occurences: int) -> Graph:
		raw = {}
		for _, stacks in self._data.items():
			for _, question in stacks.items():
				questionTime = datetime.datetime.fromtimestamp(question['creation_date'])
				for tag in question['tags']:
					if tag not in raw: raw[tag] = {'USSA': 0, 'EUAF': 0, 'ASAU': 0}
					if questionTime.time() <= t(hour = 8, minute = 0, second = 0):
						raw[tag]['USSA'] += 1
					elif questionTime.time() > t(hour = 8, minute = 0, second = 0) and questionTime.time() <= t(hour = 16, minute = 0, second = 0):
						raw[tag]['EUAF'] += 1
					else:
						raw[tag]['ASAU'] += 1
		graph = Graph()
		for tag, timezones in raw.items():
			total = sum(timezones.values())
			if total >= min_occurences:
				for timezone, occurences in timezones.items():
					if occurences != 0:
						graph.add_edge(tag, timezone, weight=occurences*100//total)
		return graph
	
	def graph_from_stacks(self) -> Graph:
		user_stacks = {}

		for stack, questions in self._data.items():
			for _, question in questions.items():
				if 'user_id' in question['owner']:
					if question['owner']['user_id'] not in user_stacks:
						user_stacks[question['owner']['user_id']] = set()
					user_stacks[question['owner']['user_id']].add(stack)

		for k, v in user_stacks.items():
			if len(v) > 5: print(k,v)
				
		graph = Graph()
		for _, stacks in user_stacks.items():
			for stackA in stacks:
				for stackB in stacks:
					if stackA < stackB:
						graph.add_edge(stackA, stackB)
		return graph

	def graph_from_rating(self) -> Graph:
		graph = Graph()
		ratings = []
		for stack, questions in self._data.items():
			for _, question in questions.items():
				ratings.append(question['score'])
		p0 = np.percentile(ratings,20)
		p1 = np.percentile(ratings,40)
		p2 = np.percentile(ratings,60)
		p3 = np.percentile(ratings,80)
		p4 = np.percentile(ratings,100)
		for stack, questions in self._data.items():
			for _, question in questions.items():
				if question['score'] <= p0:
					for tag in question['tags']:
						graph.add_edge(tag,'very bad')
				elif question['score'] <= p1:
					for tag in question['tags']:
						graph.add_edge(tag,'bad')
				elif question['score'] <= p2:
					for tag in question['tags']:
						graph.add_edge(tag,'ok')
				elif question['score'] <= p3:
					for tag in question['tags']:
						graph.add_edge(tag,'good')
				else : #question['score'] <= p4
					for tag in question['tags']:
						graph.add_edge(tag,'very good')
		return graph

class StackFetcher:

	def __init__(self):
		self._questions = UniqueQuestions()

	def fetch(self, stack_apis: [StackAPI], iterations: int = 1, time_intvl: int = 3600, time_diff: int = 0) -> int:
		ts = int(time.time())
		for stack_api in stack_apis:
			print('fetching from:', stack_api._name)
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
			print(self._questions)
			
	def get_uniqueQuestions(self) -> UniqueQuestions:
		return self._questions
#
# ----------------------------------------------------------------------
#
def get_stack_names() -> list:
		# may change to REST request
		# http://api.stackexchange.com/2.2/sites
		#
		# -> [request[items][i]['api_site_parameter'] for i in range(len(request[items])))]

		return ['stackoverflow', 'serverfault', 'superuser', 'meta',
			'webapps', 'webapps.meta', 'gaming', 'gaming.meta',
			'webmasters', 'webmasters.meta', 'cooking', 'cooking.meta',
			'gamedev', 'gamedev.meta', 'photo', 'photo.meta', 'stats',
			'stats.meta', 'math', 'math.meta', 'diy', 'diy.meta',
			'meta.superuser', 'meta.serverfault', 'gis', 'gis.meta',
			'tex', 'tex.meta', 'askubuntu', 'meta.askubuntu']

def stack_apis_from_names(stack_names: list) -> list:
	return [StackAPI(stack_name) for stack_name in stack_names]

if __name__ == '__main__':
	sf = StackFetcher()

	sf.json_load_questions('qs.json')


#	stack_names = get_stack_names()
#	stack_apis = stack_apis_from_names(stack_names)
#	for stack_api in stack_apis:
#		sf.fetch([stack_api], iterations=5, time_intvl=3600*24*30, time_diff=3600*24*30*7)
#		sf.json_dump_questions('qs.json')

	uq = sf.get_uniqueQuestions()

	graph_tags = uq.graph_from_tags()
	graph_tags.filter_min_occurences(2)

	graph_timezones = uq.graph_from_timezones()
	graph_timezones.filter_min_occurences(2)

	graph_timezones_norm = uq.graph_from_timezones_normalized_filtered(min_occurences=100)

	graph_stacks = uq.graph_from_stacks()

	graph_rating = uq.graph_from_rating()
	graph_rating.filter_min_occurences(2)
	
	csv_tag_output = graph_tags.to_csvOutput()
	csv_timezone_output = graph_timezones.to_csvOutput()
	csv_timezone_norm = graph_timezones_norm.to_csvOutput()
	csv_stack_output = graph_stacks.to_csvOutput()
	csv_rating_output = graph_rating.to_csvOutput()
	
	csv_tag_output.export_to_csv('edge_tag.csv', 'node_tag.csv')
	csv_timezone_output.export_to_csv('edge_timezone.csv', 'node_timezone.csv')
	csv_timezone_norm.export_to_csv('edge_timezone_norm.csv', 'node_timezone_norm.csv')
	csv_stack_output.export_to_csv('edge_stack.csv', 'node_stack.csv')
	csv_rating_output.export_to_csv('edge_rating.csv', 'node_rating.csv')
