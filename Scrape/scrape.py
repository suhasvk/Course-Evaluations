# scrape.py
import requests
import re
# from bs4 import BeautifulSoup
import itertools
from basic_extraction_flow import NewStyleSurveyItem, OldStyleSurveyItem, DistributionPage
import copy

main_path = ''
#ENTER KERBEROS USERNAME AND PASSWORD IN "__credentials.txt" IN ORDER TO RUN THIS SCRIPT

with open('__credentials.txt','r') as f:
	un = f.readline().rstrip('\n') #KERBEROS USERNAME
	pw = f.readline().rstrip('\n') #KERBEROS PASSWORD

######################################################################################################################
# Function: write_page
#	writes a file to disk
# Recieves: 
#	content: a (string) representation of the file
#	name: the desired name of the saved file
# Returns: 
# 	N/A
######################################################################################################################
def write_page(content, name = ""):
	"""Generates .html file from content string. Useful for debugging."""
	f = open(main_path+"__test"+name+".html","w")
	f.write(content)
	f.close()

######################################################################################################################
# Function: get_SAML_data
# 	parses an html file containing an openSAML response into a dictionary that contains the necessary data to successfuly perform the SAML response and
# 	view the desired page
# Recieves: 
#	pageString: the page containing the SAML data, and as well as the link where we'll send our response
#	session: the Session object (cf. Requests.py) that performed the initial request which received the openSAML response
# Returns: 
# 	A dictionary containing two keys, 'RelayState' and 'SAMLResponse', which correspond directly to the query string of a successful SAML response
######################################################################################################################
def get_SAML_data(pageString, session):
	relayState = re.findall('(?<=name="RelayState" value=")\S*(?=")', pageString)[0].replace('&#x3a;',':').replace('&amp;','&')
	SAMLResponse = re.findall('(?<=name="SAMLResponse" value=")\S*(?=")', pageString)[0]
	nextAction = re.findall('(?<=action=")\S*(?=")', pageString)[0].replace('&#x3a;',':').replace('&#x2f;','/')
	session.headers.update({'Referer':'https://idp.mit.edu:446/idp/profile/SAML2/Redirect/SSO'}) 
	return {'RelayState':relayState, 'SAMLResponse': SAMLResponse}, nextAction


#take in url, live session object- already authenticated,  dictionary<field, value> 
def getHtmlAsBeautifulSoupObject(baseUrl, session, paramMap):
        html = session.get(baseUrl, data=paramMap)
        return BeautifulSoup(html)




def setUpSessionWithCredentials(initialUrl):
	#--------------#
	#GETTING ACCESS#
	#--------------#

	#CREATES SESSION
	session = requests.Session()


	#DOES INITIAL URL ATTEMPT; EXPECTS REDIRECT TO TOUCHTONE LOGIN PAGE
	red1 = session.get(initialUrl)


	#ATTEMPTS LOGIN WITH USERNAME AND PASSWORD

	#This gets the url at which to submit the login form
	action = re.findall('(?<=action=")\S*(?=")', red1.content)[1].replace('&amp;','&')
	#This dictionary contains the query string to submit to the url
	payload = {'j_username':un, 'j_password':pw, 'Submit':'Login'}
	#Perform the POST request
	red2 = session.post(action, data = payload) #this gives us an opensaml response 


	#NOW WE NEED TO RESPOND TO THE SERVER'S OPENSAML RESPONSE, WHICH IS AN ADDITIONAL SECURITY MEASURE
	#Extract the relevant information from the page so as to attempt the SAML response
	payload_2, nextAction = get_SAML_data(red2.content, session)
	#Make the SAML response, and get the resulting page, which is the original page we were attempting to visit
	red3 = session.post(nextAction, data=payload_2)

	return session



######################################################################################################################
# Function: scrape
# 	retrieves survey item objects for a requested set of course evaluation surveys
# Recieves: 
#	url - the url of any protected mit page. By accessing it, we'll authenticate ourselves
#	dateRange - the range of years (represented as an iterable of integers) from which we'd like to retrieve surveys
# 	courseNumbers - a list of the course numbers (strings, i.e. '18.02') for which we'd like to get survey data
# 	semesters - a sublist of ['FA','SP'] which identifies which semesters (fall or spring, or both) we'd like to retrieve surveys from
# Returns: 
# 	surveyItemList - a list of survey item objects (NewStyleSurveyItem or OldStyleSurveyItem), which may be used to extract information from the received survey pages
######################################################################################################################
def scrape(url, dateRange, courseNumbers, semesters = ['FA','SP']):
	global main_path, un, pw

	print 'logging in'
	session = setUpSessionWithCredentials(url)
	

	#-----------------------------#
	#VISITING PAGES, SCRAPING DATA#
	#-----------------------------#
	#NOW THE REQUESTS SESSION HAS THE COOKIES IT NEEDS TO ACCESS WHATEVER CONTENT YOU CAN VIEW, SO DO WHAT YOU WANT TO

	#This is a list that will contain the objects that correspond to the requested surveys
	surveyItemList = []
	webPageGetterFunction = lambda url: getHtmlAsBeautifulSoupObject(url, s, {})

	#For every triple (course#, year, semester) in the requested range
	#for window in itertools.product(courseNumbers, dateRange, semesters):

	print 'getting course data'

	for (year, courseNumber, semester) in itertools.product(courseNumbers, dateRange, semesters):

		#Following line searches evaluations for the given (course, year, semester)
                searchUrl = 'https://edu-apps.mit.edu/ose-rpt/subjectEvaluationSearch.htm?termId='+ year + semester +'&departmentId=&subjectCode='+ courseNumber+ '&instructorName=&search=Search'
		search_page = session.get('https://edu-apps.mit.edu/ose-rpt/subjectEvaluationSearch.htm?termId='+ year + semester +'&departmentId=&subjectCode='+ courseNumber+ '&instructorName=&search=Search')

                
#search url looks like: https://edu-apps.mit.edu/ose-rpt/subjectEvaluationSearch.htm?termId=&departmentId=&subjectCode=21M.303&instructorName=&search=Search
#https://edu-apps.mit.edu/ose-rpt/subjectEvaluationSearch.htm?termId=2015SP&departmentId=&subjectCode=21M.303&instructorName=&search=Search

	

		#If course wasn't offered that semester, do nothing.
		if 'No records found' in search_page.content: 
			continue

		#This regex matches if the link we retrieved is to old-style course evaluation.
		links = re.findall('(?<=<a href=")https://\S*(?=")',search_page.content) 

		#If there's a match, flag as old and get link.
		if len(links) > 0: 
			link = links[0]
			old = True

		#Otherwise, flag as new and get link.
		else: 
			link = 'https://edu-apps.mit.edu/ose-rpt/'+ re.findall('(?<=<a href=")subjectEvaluationReport\S*(?=")',search_page.content)[0]
			old = False

		print link

		
		#If old, follow redirect through to page.
		if old:
			new_session = copy.deepcopy(session) #Must preserve current state of cookies in order for SAML response to make sense

			next = new_session.get(links[0])
			payload, nextAction = get_SAML_data(next.content, new_session)
			eval_page = new_session.post(nextAction, data=payload)
			item = OldStyleSurveyItem(eval_page.content)
			surveyItemList.append(item)

		#Otherwise, just get the page
		else:
			eval_page = session.get(link)
			item = NewStyleSurveyItem(eval_page.content, webPageGetterFunction)

			#new link looks like: 
			#https://edu-apps.mit.edu/ose-rpt/subjectEvaluationReport.htm?surveyId=489&subjectGroupId=06B2B712C0DA071DE0533D2F0912587C&subjectId=21M.303

			#distributionUrl looks like: 
			#https://edu-apps.mit.edu/ose-rpt/frequencyDistributionReport.htm?va=&subjectId=21M.303&surveyId=489&subjectGroupId=06B2B712C0DA071DE0533D2F0912587C&questionId=5291&questionGroupId=4391&typeKey=subject

			surveyItemList.append(item)
			distributionPageList = []
			for link in item.getRawRatingsInfo()[1]: 
				distribution = DistributionPage(session.get(url+link).content)
				distributionPageList.append(distribution)

			item.addDistributionPages(distributionPageList)



	return surveyItemList


if __name__ == '__main__':

	surveyItemList = scrape("https://edu-apps.mit.edu/ose-rpt/", ['21M.303'], map(str, range(2013,2014)))

