# __basic_extraction_flow.py
# Suhas V. & Abraham Quintero| Jan 21, 2015

from bs4 import BeautifulSoup
import sqlite3
import re


class NewStyleSurveyItem:	
	def __init__(self, file_str, webPageGetterFunction = None):
		"""Initializes object. 
		'file_str' <- html file of survey page, represented as a unicode string."""

		self.soup = BeautifulSoup(file_str)
		self.distributionList = []
		self.webPageGetterFunction = webPageGetterFunction

        def __str__(self):
		return self.soup.prettify().encode('utf-8')


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

	def getRawRatingsInfo(self):
		#finds all <a href = '... nodes in DOM
		links = filter(lambda x: x.has_attr("href"),self.soup.findAll("a"))

		#gets 'href' property of each link, and filters these down to just those containing 'subjectGroupId'
		#these happen to be the ones we care about
		dataLinks = filter(lambda x: 'subjectGroupId' in x, map(lambda y: y['href'], links)) 

		instructorPageLinks = filter(lambda lnk: 'instructorEvaluationReport' in lnk, dataLinks)
		questionPageLinks = filter(lambda lnk: 'frequencyDistributionReport' in lnk, dataLinks)
		return (instructorPageLinks, questionPageLinks)

	def addDistributionPages(self, distributionPageList):
		self.distributionList += distributionPageList

	def dump(self, cursor):
		pass

class DistributionPage:
	def __init__(self, file_str):
		self.soup = BeautifulSoup(file_str)
		self.criterion = self.soup.h3.get_text()
		self.distribution = map(lambda x: x.get_text().split(), self.soup.find_all('li',{'class':'scale'}))
		#graph is a bunch of <li class="scale"> elems...

class OldStyleSurveyItem:
	def __init__(self, file_str):
		self.soup = BeautifulSoup(file_str)

	def getClassRatings(self):
		raw_stuff = map(lambda x: x.text, self.soup.findAll("td", {'valign':'top'}))[1:]

if __name__ == '__main__':
	pass
