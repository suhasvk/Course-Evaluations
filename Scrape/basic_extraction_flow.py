# __basic_extraction_flow.py
# Suhas V. | Jan 21, 2015

from bs4 import BeautifulSoup
import sqlite3
import re



class NewStyleSurveyItem:
	def __init__(self, file_str, session = None):
		"""Initializes object. 
		'file_str' <- html file of survey page, represented as a unicode string."""

		self.soup = BeautifulSoup(file_str)

	def getProfs(self):
		links = filter(lambda x: x.has_attr("href"),self.soup.findAll("a"))
		data_links = filter(lambda x: 'subjectGroupId' in x['href'], links)
		return list(set([x.text for x in data_links if 'instructor' in x["href"]]))

	def getSemester(self): 
		"""Returns course semester, i.e. '<Season> <Year>'"""

		#Survey window info is stored in the 'h2' child of '.subjectTitle' table
		return ' '.join(self.soup.find('td', class_='subjectTitle').h2.text.split()[2:4])

	def getName(self):
		"""Returns course title, i.e. '<Course #> <Course Name>'"""

		def clean_wspace(s):
			return ' '.join(s.split())

		#Title is stored in 'h1' child of 'lsubjectTitle' table
		return clean_wspace(self.soup.find('td', class_='subjectTitle').h1.text)

	def getRespondentInfo(self):
		"Returns dict: {'<Field Name>': "

		#Finds all '.tooltip' elements, and gets the relevant info out of them
		l = map(lambda x: re.split('<strong>|</strong>|<a', str(x))[1:3], self.soup.body.findAll('p', class_='tooltip'))
		return {k[0][:-1]: k[1] for k in l}



	def getCourse(self):
		return self.getName().split('.')[0]

	def getRatings(self):
		links = filter(lambda x: x.has_attr("href"),self.soup.findAll("a"))
		data_links = filter(lambda x: 'subjectGroupId' in x['href'], links)
		inds = self.soup.findAll("table", { "class" : "indivQuestions" })
		k = filter(lambda x: not any(z.has_attr("href") for z in x.findAll("a")), inds)
		return (links, data_links, inds, k)

	def dump(self, cursor):
		pass

class DistributionPage:
	def __init__(self, file_str):
		self.soup = BeautifulSoup(file_str)
		self.criterion = self.soup.h3.get_text()
		self.distribution = map(lambda x: x.get_text().split(), soup.find_all('li',{'class':'scale'}))
		#graph is a bunch of <li class="scale"> elems...

class OldStyleSurveyItem:
	def __init__(self, file_str):
		self.soup = BeautifulSoup(file_str)

	def getClassRatings(self):
		raw_stuff = map(lambda x: x.text, self.soup.findAll("td", {'valign':'top'}))[1:]

if __name__ == '__main__':
	pass