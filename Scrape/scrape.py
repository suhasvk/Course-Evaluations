# mitscrape.py
import requests as r
import re
# from bs4 import BeautifulSoup
import itertools as i
from basic_extraction_flow import NewStyleSurveyItem, OldStyleSurveyItem
import copy

main_path = ''
#ENTER KERBEROS USERNAME AND PASSWORD BELOW TO SCRAPE
#NOTE: IF YOU FILL IN INFO BELOW, SAVE AS 'use_scrape.py' SO GIT WILL IGNORE IT--DON'T PUSH
with open('__credentials.txt','r') as f:
	un = f.readline().rstrip('\n') #KERBEROS USERNAME
	pw = f.readline().rstrip('\n') #KERBEROS PASSWORD


def write_page(content, name = ""):
	"""Generates .html file from content string. Useful for debugging."""
	f = open(main_path+"__test"+name+".html","w")
	f.write(content)
	f.close()

def get_SAML_data(page_str, session):
	relayState = re.findall('(?<=name="RelayState" value=")\S*(?=")', page_str)[0].replace('&#x3a;',':').replace('&amp;','&')
	SAMLResponse = re.findall('(?<=name="SAMLResponse" value=")\S*(?=")', page_str)[0]
	nextAction = re.findall('(?<=action=")\S*(?=")', page_str)[0].replace('&#x3a;',':').replace('&#x2f;','/')
	session.headers.update({'Referer':'https://idp.mit.edu:446/idp/profile/SAML2/Redirect/SSO'}) 
	return {'RelayState':relayState, 'SAMLResponse': SAMLResponse}, nextAction
	

def scrape(url):
	global main_path, un, pw

	#--------------#
	#GETTING ACCESS#
	#--------------#

	#CREATES SESSION
	session = r.Session()


	#DOES INITIAL URL ATTEMPT; EXPECTS REDIRECT
	red1 = session.get(url)

	#ATTEMPTS LOGIN WITH USERNAME AND PASSWORD
	action = re.findall('(?<=action=")\S*(?=")', red1.content)[1].replace('&amp;','&')
	payload = {'j_username':un, 'j_password':pw, 'Submit':'Login'}
	red2 = session.post(action, data = payload)


	#ATTEMPTS OPENSAML RESPONSE
	payload_2, nextAction = get_SAML_data(red2.content, session)
	red3 = session.post(nextAction, data=payload_2)

	 
	#THIS OUTPUTS FINAL PAGE (THE ONE YOU WANTED TO ACCESS)
	# write_page(red3.content)

	#-----------------------------#
	#VISITING PAGES, SCRAPING DATA#
	#-----------------------------#
	#NOW THE REQUESTS SESSION HAS THE COOKIES IT NEEDS TO ACCESS WHATEVER CONTENT YOU CAN VIEW, SO DO WHAT YOU WANT TO
	courses = ['21M.303']
	years = map(str, range(1998,2014))
	semesters = ['FA','SP']

	for window in i.product(courses, years, semesters):
		#Following line searches evaluations for a given (course, year, semester)
		search_page = session.get('https://edu-apps.mit.edu/ose-rpt/subjectEvaluationSearch.htm?termId=%s&departmentId=&subjectCode=%s&instructorName=&search=Search' % (window[1]+window[2], window[0]))

		#If course wasn't offered that semester, do nothing.
		if 'No records found' in search_page.content: 
			continue

		#Following regex matches if link is to old-style course evaluation.
		links = re.findall('(?<=<a href=")https://\S*(?=")',search_page.content) 

		#If there's a match, flag as old and get link.
		if len(links) > 0: 
			link = links[0]
			old = True

		#Otherwise, flag as new and get link.
		else: 
			link = 'https://edu-apps.mit.edu/ose-rpt/'+ re.findall('(?<=<a href=")subjectEvaluationReport\S*(?=")',search_page.content)[0]
			old = False

		#If old, follow redirect through to page.
		if old:
			new_session = copy.deepcopy(session) #Must preserve current state of cookies in order for SAML response to make sense

			print window[1]+window[2],'OLD' #DEBUG
			next = new_session.get(links[0])
			payload, nextAction = get_SAML_data(next.content, new_session)
			eval_page = new_session.post(nextAction, data=payload)
			item = OldStyleSurveyItem(eval_page.content)

		#Otherwise, just get
		else:
			eval_page = session.get(link)
			item = NewStyleSurveyItem(eval_page.content, session)

if __name__ == '__main__':
	scrape("https://edu-apps.mit.edu/ose-rpt/")

