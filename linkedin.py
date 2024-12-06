import time,math,random,os
import utils,constants,config
import pickle, hashlib

from selenium import webdriver
from selenium.webdriver.common.by import By

from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from datetime import datetime

class Linkedin:
    def __init__(self):
            utils.prYellow("🤖 Thanks for using Easy Apply Jobs bot, for more information you can visit our site - www.automated-bots.com")
            utils.prYellow("🌐 Bot will run in Chrome browser and log in Linkedin for you.")
            self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()),options=utils.chromeBrowserOptions())
            self.cookies_path = f"{os.path.join(os.getcwd(),'cookies')}/{self.getHash(config.email)}.pkl"
            self.driver.get('https://www.linkedin.com')
            self.loadCookies()

            if not self.isLoggedIn():
                self.driver.get("https://www.linkedin.com/login?trk=guest_homepage-basic_nav-header-signin")
                utils.prYellow("🔄 Trying to log in Linkedin...")
                try:    
                    self.driver.find_element("id","username").send_keys(config.email)
                    time.sleep(2)
                    self.driver.find_element("id","password").send_keys(config.password)
                    time.sleep(2)
                    self.driver.find_element("xpath",'//button[@type="submit"]').click()
                    time.sleep(30)
                except:
                    utils.prRed("❌ Couldn't log in Linkedin by using Chrome. Please check your Linkedin credentials on config files line 7 and 8.")

                self.saveCookies()
            # start application
            self.linkJobApply()

    def getHash(self, string):
        return hashlib.md5(string.encode('utf-8')).hexdigest()

    def loadCookies(self):
        if os.path.exists(self.cookies_path):
            cookies =  pickle.load(open(self.cookies_path, "rb"))
            self.driver.delete_all_cookies()
            for cookie in cookies:
                self.driver.add_cookie(cookie)

    def saveCookies(self):
        pickle.dump(self.driver.get_cookies() , open(self.cookies_path,"wb"))
    
    def isLoggedIn(self):
        self.driver.get('https://www.linkedin.com/feed')
        try:
            self.driver.find_element(By.XPATH,'//*[@id="ember14"]')
            return True
        except:
            pass
        return False 
    
    def generateUrls(self):
        if not os.path.exists('data'):
            os.makedirs('data')
        try: 
            with open('data/urlData.txt', 'w',encoding="utf-8" ) as file:
                linkedinJobLinks = utils.LinkedinUrlGenerate().generateUrlLinks()
                for url in linkedinJobLinks:
                    file.write(url+ "\n")
            utils.prGreen("✅ Apply urls are created successfully, now the bot will visit those urls.")
        except:
            utils.prRed("❌ Couldn't generate urls, make sure you have editted config file line 25-39")

    def linkJobApply(self):
        self.generateUrls()
        countApplied = 0
        countJobs = 0

        urlData = utils.getUrlDataFile()

        for url in urlData:        
            self.driver.get(url)
            time.sleep(random.uniform(1, constants.botSpeed))

            totalJobs = self.driver.find_element(By.XPATH,'//small').text 
            totalPages = utils.jobsToPages(totalJobs)

            urlWords =  utils.urlToKeywords(url)
            lineToWrite = "\n Category: " + urlWords[0] + ", Location: " +urlWords[1] + ", Applying " +str(totalJobs)+ " jobs."
            self.displayWriteResults(lineToWrite)

            for page in range(totalPages):
                currentPageJobs = constants.jobsPerPage * page
                url = url +"&start="+ str(currentPageJobs)
                self.driver.get(url)
                time.sleep(random.uniform(1, constants.botSpeed))

                offersPerPage = self.driver.find_elements(By.XPATH, '//li[@data-occludable-job-id]')
                offerIds = [(offer.get_attribute(
                    "data-occludable-job-id").split(":")[-1]) for offer in offersPerPage]
                time.sleep(random.uniform(1, constants.botSpeed))

                for offer in offersPerPage:
                    if not self.element_exists(offer, By.XPATH, ".//*[contains(text(), 'Applied')]"):
                        offerId = offer.get_attribute("data-occludable-job-id")
                        offerIds.append(int(offerId.split(":")[-1]))

                for jobID in offerIds:
                    offerPage = 'https://www.linkedin.com/jobs/view/' + str(jobID)
                    self.driver.get(offerPage)
                    time.sleep(random.uniform(1, constants.botSpeed))

                    countJobs += 1

                    jobProperties = self.getJobProperties(countJobs)
                    if "blacklisted" in jobProperties: 
                        lineToWrite = jobProperties + " | " + "* 🤬 Blacklisted Job, skipped!: " +str(offerPage)
                        self.displayWriteResults(lineToWrite)
                    
                    else :                    
                        easyApplybutton = self.easyApplyButton()

                        if easyApplybutton is not False:
                            easyApplybutton.click()
                            time.sleep(random.uniform(1, constants.botSpeed))
                            
                            try:
                                self.chooseResume()
                                self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Submit application']").click()
                                time.sleep(random.uniform(1, constants.botSpeed))

                                lineToWrite = jobProperties + " | " + "* 🥳 Just Applied to this job: "  +str(offerPage)
                                self.displayWriteResults(lineToWrite)
                                countApplied += 1

                            except:
                                try:
                                    self.driver.find_element(By.CSS_SELECTOR,"button[aria-label='Continue to next step']").click()
                                    time.sleep(random.uniform(1, constants.botSpeed))
                                    self.chooseResume()
                                    comPercentage = self.driver.find_element(By.XPATH,'html/body/div[3]/div/div/div[2]/div/div/span').text
                                    percenNumber = int(comPercentage[0:comPercentage.index("%")])
                                    result = self.applyProcess(percenNumber,offerPage)
                                    lineToWrite = jobProperties + " | " + result
                                    self.displayWriteResults(lineToWrite)
                                
                                except Exception: 
                                    self.chooseResume()
                                    lineToWrite = jobProperties + " | " + "* 🥵 Cannot apply to this Job! " +str(offerPage)
                                    self.displayWriteResults(lineToWrite)
                        else:
                            lineToWrite = jobProperties + " | " + "* 🥳 Already applied! Job: " +str(offerPage)
                            self.displayWriteResults(lineToWrite)


            utils.prYellow("Category: " + urlWords[0] + "," +urlWords[1]+ " applied: " + str(countApplied) +
                  " jobs out of " + str(countJobs) + ".")
        
        utils.donate(self)

    def chooseResume(self):
        try:
            self.driver.find_element(
                By.CLASS_NAME, "jobs-document-upload__title--is-required")
            resumes = self.driver.find_elements(
                By.XPATH, "//div[contains(@class, 'ui-attachment--pdf')]")
            if (len(resumes) == 1 and resumes[0].get_attribute("aria-label") == "Select this resume"):
                resumes[0].click()
            elif (len(resumes) > 1 and resumes[config.preferredCv-1].get_attribute("aria-label") == "Select this resume"):
                resumes[config.preferredCv-1].click()
            elif (type(len(resumes)) != int):
                utils.prRed(
                    "❌ No resume has been selected please add at least one resume to your Linkedin account.")
        except:
            pass

    def getJobProperties(self, count):
        textToWrite = ""
        jobTitle = ""
        jobLocation = ""
        companyName = ""
        timeAgoPosted = ""
        jobDescription = ""

        try:
            # Updated selector for job title
            jobTitle = self.driver.find_element(By.CSS_SELECTOR, "h1.t-24.t-bold.inline").text.strip()
            res = [blItem for blItem in config.blackListTitles if (blItem.lower() in jobTitle.lower())]
            if res:
                jobTitle += " (Blacklisted title: " + ' '.join(res) + ")"
        except Exception as e:
            # If the first selector fails, try the original one as backup
            try:
                jobTitle = self.driver.find_element(By.XPATH, "//h1[contains(@class, 'job-title')]").text.strip()
            except:
                if config.displayWarnings:
                    utils.prYellow(f"⚠️ Warning in getting jobTitle: {str(e)}")
                jobTitle = ""

        try:
            # Try finding by link with the specific ember-view class and job details attribute
            companyName = self.driver.find_element(By.CSS_SELECTOR, "a.ember-view[data-view-name='job-details-about-company-name-link']").text.strip()
        except Exception as e:
            try:
                # Fallback to looking for any link with ember-view and link-without-visited-state classes
                companyName = self.driver.find_element(By.CSS_SELECTOR, "a.ember-view.link-without-visited-state").text.strip()
            except:
                try:
                    # Last attempt - just look for the ember view with inline-block
                    companyName = self.driver.find_element(By.CSS_SELECTOR, "a.ember-view.inline-block").text.strip()
                except:
                    if config.displayWarnings:
                        utils.prYellow(f"⚠️ Warning in getting companyName: {str(e)}")
                    companyName = "Unknown Company"

        try:
            # Find all spans with low-emphasis class in the primary description container
            spans = self.driver.find_elements(By.CSS_SELECTOR, ".job-details-jobs-unified-top-card__primary-description-container span.tvm__text.tvm__text--low-emphasis")
            # First span should be location
            if spans:
                jobLocation = spans[0].text.strip()
            else:
                raise Exception("No spans found")
        except Exception as e:
            # Original fallbacks
            try:
                jobLocation = self.driver.find_element(By.XPATH, "//span[contains(@class, 'topcard__flavor--bullet')]").text.strip()
            except:
                try:
                    jobLocation = self.driver.find_element(By.CLASS_NAME, "jobs-unified-top-card__bullet").text.strip()
                except:
                    if config.displayWarnings:
                        utils.prYellow(f"⚠️ Warning in getting jobLocation: {str(e)}")
                    jobLocation = "Unknown Location"

        try:
            # Get all spans with low-emphasis class in the primary description container
            description_container = self.driver.find_element(By.CSS_SELECTOR, ".job-details-jobs-unified-top-card__primary-description-container")
            spans = description_container.find_elements(By.CSS_SELECTOR, "span.tvm__text.tvm__text--low-emphasis")
            
            # The second span contains the post date (after location)
            if len(spans) >= 2:
                timeAgoPosted = spans[2].text.strip()
            else:
                raise Exception("Not enough spans found")

        except Exception as e:
            try:
                # Fallback: Try finding among any low-emphasis spans
                all_spans = self.driver.find_elements(By.CSS_SELECTOR, "span.tvm__text.tvm__text--low-emphasis")
                for span in all_spans:
                    text = span.text.strip()
                    if 'ago' in text or 'hour' in text or 'day' in text or 'week' in text or 'month' in text:
                        timeAgoPosted = text
                        break
                else:
                    timeAgoPosted = "Unknown Date"
            except:
                if config.displayWarnings:
                    utils.prYellow(f"⚠️ Warning in getting timeAgoPosted: {str(e)}")
                timeAgoPosted = "Unknown Date"
        # try:
        #     # Fetch job description
        #     jobDescriptionElement = self.driver.find_element(By.XPATH, "//div[contains(@class, 'show-more-less-html__markup')]")
        #     jobDescription = jobDescriptionElement.text[:300] + "..." if len(jobDescriptionElement.text) > 300 else jobDescriptionElement.text
        # except Exception as e:
        #     if config.displayWarnings:
        #         utils.prYellow(f"⚠️ Warning in getting jobDescription: {str(e)}")
        #     jobDescription = "Description not available"

        # Construct detailed job properties string
        textToWrite = (
            f"{count} | Job Title: {jobTitle} | Company: {companyName} | Location: {jobLocation} "
            f"| Posted: {timeAgoPosted} | Time Applied {datetime.now().strftime("%Y-%m-%d")}" #adds curr date
        )

        return textToWrite


    def easyApplyButton(self):
        try:
            time.sleep(random.uniform(1, constants.botSpeed))
            button = self.driver.find_element(By.XPATH, "//div[contains(@class,'jobs-apply-button--top-card')]//button[contains(@class, 'jobs-apply-button')]")
            EasyApplyButton = button
        except: 
            EasyApplyButton = False

        return EasyApplyButton

    def applyProcess(self, percentage, offerPage):
        applyPages = math.floor(100 / percentage) - 2 
        result = ""
        for pages in range(applyPages):  
            self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Continue to next step']").click()

        self.driver.find_element( By.CSS_SELECTOR, "button[aria-label='Review your application']").click()
        time.sleep(random.uniform(1, constants.botSpeed))

        if config.followCompanies is False:
            try:
                self.driver.find_element(By.CSS_SELECTOR, "label[for='follow-company-checkbox']").click()
            except:
                pass

        self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Submit application']").click()
        time.sleep(random.uniform(1, constants.botSpeed))

        result = "* 🥳 Just Applied to this job: " + str(offerPage)

        return result

    def displayWriteResults(self,lineToWrite: str):
        try:
            print(lineToWrite)
            utils.writeResults(lineToWrite)
        except Exception as e:
            utils.prRed("❌ Error in DisplayWriteResults: " +str(e))

    def element_exists(self, parent, by, selector):
        return len(parent.find_elements(by, selector)) > 0

start = time.time()
Linkedin().linkJobApply()
end = time.time()
utils.prYellow("---Took: " + str(round((time.time() - start)/60)) + " minute(s).")
