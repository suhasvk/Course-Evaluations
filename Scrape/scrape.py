# mitscrape.py
import requests as r
import re
import itertools as i


main_path = '/Users/suhasv/Desktop/CourseEval/Scrape/test/'
#ENTER KERBEROS USERNAME AND PASSWORD BELOW TO SCRAPE
#NOTE: IF YOU FILL IN INFO BELOW, SAVE AS 'use_scrape.py' SO GIT WILL IGNORE IT--DON'T PUSH
pw = '' #KERBEROS PASSWORD
un = '' #KERBEROS USERNAME

def write_page(content, name = ""):
	"""Generates .html file from content string. Useful for debugging."""
	f = open(main_path+"test"+name+".html","w")
	f.write(content)
	f.close()

def scrape(url):
	global main_path, un, pw

	#--------------#
	#GETTING ACCESS#
	#--------------#

	#CREATES SESSION
	s = r.Session()


	#DOES INITIAL URL ATTEMPT; EXPECTS REDIRECT
	red1 = s.get(url)

	#ATTEMPTS LOGIN WITH USERNAME AND PASSWORD
	action = re.findall('(?<=action=")\S*(?=")', red1.content)[1].replace('&amp;','&')
	payload = {'j_username':un, 'j_password':pw, 'Submit':'Login'}
	red2 = s.post(action, data = payload)


	#ATTEMPTS OPENSAML RESPONSE
	relayState = re.findall('(?<=name="RelayState" value=")\S*(?=")', red2.content)[0].replace('&#x3a;',':').replace('&amp;','&')
	SAMLResponse = re.findall('(?<=name="SAMLResponse" value=")\S*(?=")', red2.content)[0]
	nextAction = re.findall('(?<=action=")\S*(?=")', red2.content)[0].replace('&#x3a;',':').replace('&#x2f;','/')
	s.headers.update({'Referer':'https://idp.mit.edu:446/idp/profile/SAML2/Redirect/SSO'}) 
	payload_2 = {'RelayState':relayState, 'SAMLResponse': SAMLResponse}
	red3 = s.post(nextAction, data=payload_2)

	 
	#THIS OUTPUTS FINAL PAGE (THE ONE YOU WANTED TO ACCESS)
	# write_page(red3.content)

	#-----------------------------#
	#VISITING PAGES, SCRAPING DATA#
	#-----------------------------#
	#NOW THE REQUESTS SESSION HAS THE COOKIES IT NEEDS TO ACCESS WHATEVER CONTENT YOU CAN VIEW, SO DO WHAT YOU WANT TO
	courses = ['12.602', '12.002']
	years = map(str, range(1998,2014))
	semesters = ['FA','SP']

	for cls in i.product(courses, years, semesters):

		#Following line searches evaluations for a given (course, year, semester)
		search_page = s.get('https://edu-apps.mit.edu/ose-rpt/subjectEvaluationSearch.htm?termId=%s&departmentId=&subjectCode=%s&instructorName=&search=Search' % (cls[1]+cls[2], cls[0]))

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
			continue #TODO

		#Visit evaluation page.
		eval_page = s.get(link)

		write_page(eval_page.content, 'search%s' % reduce(lambda x,y: x+y, cls)) #TEST

if __name__ == '__main__':
	scrape("https://edu-apps.mit.edu/ose-rpt/")

