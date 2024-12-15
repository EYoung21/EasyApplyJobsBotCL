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
        try:
            self.generateUrls()
            countApplied = 0
            countJobs = 0

            urlData = utils.getUrlDataFile()

            for url in urlData:        
                try:
                    print(f"\nAttempting to process job URL: {url}")
                    self.driver.get(url)
                    time.sleep(random.uniform(1, constants.botSpeed))

                    try:
                        totalJobs = self.driver.find_element(By.XPATH,'//small').text 
                        print(f"Found {totalJobs} total jobs")
                        totalPages = utils.jobsToPages(totalJobs)
                    except Exception as e:
                        print(f"Error getting total jobs: {str(e)}")
                        continue

                    urlWords = utils.urlToKeywords(url)
                    lineToWrite = "\n Category: " + urlWords[0] + ", Location: " +urlWords[1] + ", Applying " +str(totalJobs)+ " jobs."
                    self.displayWriteResults(lineToWrite)

                    for page in range(totalPages):
                        try:
                            currentPageJobs = constants.jobsPerPage * page
                            pageUrl = url + "&start=" + str(currentPageJobs)
                            print(f"\nProcessing page {page + 1}, URL: {pageUrl}")
                            self.driver.get(pageUrl)
                            time.sleep(random.uniform(1, constants.botSpeed))

                            offersPerPage = self.driver.find_elements(By.XPATH, '//li[@data-occludable-job-id]')
                            print(f"Found {len(offersPerPage)} jobs on this page")

                            offerIds = []
                            for offer in offersPerPage:
                                try:
                                    if not self.element_exists(offer, By.XPATH, ".//*[contains(text(), 'Applied')]"):
                                        offerId = offer.get_attribute("data-occludable-job-id")
                                        if offerId:
                                            offerIds.append(int(offerId.split(":")[-1]))
                                except Exception as e:
                                    print(f"Error processing offer: {str(e)}")
                                    continue

                            for jobID in offerIds:
                                try:
                                    print(f"\nProcessing job ID: {jobID}")
                                    offerPage = 'https://www.linkedin.com/jobs/view/' + str(jobID)
                                    self.driver.get(offerPage)
                                    time.sleep(random.uniform(1, constants.botSpeed))

                                    countJobs += 1

                                    # Check if easy apply button exists before proceeding
                                    easyApplyButton = self.easyApplyButton()
                                    if easyApplyButton is False:
                                        print("No Easy Apply button found for this job")
                                        continue

                                    jobProperties = self.getJobProperties(countJobs)
                                    if "blacklisted" in jobProperties: 
                                        lineToWrite = jobProperties + " | " + "* 🤬 Blacklisted Job, skipped!: " + str(offerPage)
                                    else:
                                        print("Found Easy Apply button, attempting to click")
                                        easyApplyButton.click()
                                        time.sleep(random.uniform(1, constants.botSpeed))
                                        
                                        # Add debug output before apply process
                                        print("Starting application process...")
                                        try:
                                            # Try to find phone number field immediately after clicking Easy Apply
                                            phone_result = self.fillPhoneNumber()
                                            print(f"Phone number fill result: {phone_result}")
                                            
                                            result = self.applyProcess(100, offerPage)  # Assume 100% for single page
                                            lineToWrite = jobProperties + " | " + result
                                            countApplied += 1
                                        except Exception as apply_error:
                                            print(f"Error in application process: {str(apply_error)}")
                                            lineToWrite = jobProperties + " | " + "* 🥵 Cannot apply to this Job! " + str(offerPage)

                                    self.displayWriteResults(lineToWrite)

                                except Exception as job_error:
                                    print(f"Error processing job ID {jobID}: {str(job_error)}")
                                    continue

                        except Exception as page_error:
                            print(f"Error processing page {page}: {str(page_error)}")
                            continue

                except Exception as url_error:
                    print(f"Error processing URL {url}: {str(url_error)}")
                    continue

        except Exception as main_error:
            print(f"Major error in linkJobApply: {str(main_error)}")

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
            f"| Posted: {timeAgoPosted} | Time Applied {datetime.now().strftime('%Y-%m-%d')}"  # Note the single quotes
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

    def fillPhoneNumber(self):
        """Attempts to find and fill phone number field using LinkedIn's specific format"""
        print("Starting phone number fill attempt...")
        
        phone_selectors = [
            "input[id*='phoneNumber-nationalNumber']",
            "input[class*='fb-dash-form-element__error-field']",
            ".artdeco-text-input--input[id*='phoneNumber']",
        ]
        
        try:
            for selector in phone_selectors:
                print(f"Trying selector: {selector}")
                phone_inputs = self.driver.find_elements(By.CSS_SELECTOR, selector)
                print(f"Found {len(phone_inputs)} elements with this selector")
                
                if phone_inputs:
                    for phone_input in phone_inputs:
                        try:
                            print("Found phone input field, attempting to fill...")
                            # Scroll and wait
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", phone_input)
                            time.sleep(2)  # Slightly longer wait
                            
                            # Clear and click
                            print("Clearing field...")
                            phone_input.clear()
                            print("Clicking field...")
                            phone_input.click()
                            time.sleep(1)
                            
                            if hasattr(config, 'Phone') and config.Phone.strip():
                                print(f"Attempting to input phone number: {config.Phone}")
                                # Try alternative input methods if regular sendKeys fails
                                try:
                                    # Method 1: Regular send_keys
                                    phone_input.send_keys(config.Phone)
                                except:
                                    try:
                                        # Method 2: JavaScript executor
                                        self.driver.execute_script("arguments[0].value = arguments[1];", phone_input, config.Phone)
                                    except Exception as js_error:
                                        print(f"JavaScript input failed: {str(js_error)}")
                                        return False
                                
                                print("Successfully filled phone number")
                                return True
                            else:
                                print("No phone number found in config!")
                                return False
                        except Exception as input_error:
                            print(f"Error filling specific input: {str(input_error)}")
                            continue
            
            print("No phone number field found with any selector")
            return False
        except Exception as e:
            print(f"Error in fillPhoneNumber: {str(e)}")
            return False

    def applyProcess(self, percentage, offerPage):
        print("\n=== Starting application process ===")
        applyPages = math.floor(100 / percentage) - 2
        result = ""
        
        try:
            # First, let's see what's on the page
            print("Current page elements:")
            page_source = self.driver.page_source
            if 'phoneNumber' in page_source:
                print("Phone number field detected in page source")
            if 'nationalNumber' in page_source:
                print("National number field detected in page source")
                
            # Try to fill phone
            phone_result = self.fillPhoneNumber()
            print(f"Phone number fill attempt result: {phone_result}")

            for pages in range(applyPages):
                print(f"Handling page {pages + 1} of {applyPages}")
                try:
                    next_button = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Continue to next step']")
                    next_button.click()
                    time.sleep(random.uniform(1, constants.botSpeed))
                except Exception as next_error:
                    print(f"Error clicking next button: {str(next_error)}")
                    raise

            print("Attempting to click review button")
            review_button = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Review your application']")
            review_button.click()
            time.sleep(random.uniform(1, constants.botSpeed))

            if config.followCompanies is False:
                try:
                    follow_checkbox = self.driver.find_element(By.CSS_SELECTOR, "label[for='follow-company-checkbox']")
                    follow_checkbox.click()
                except Exception as follow_error:
                    print(f"Warning - Could not uncheck follow company: {str(follow_error)}")

            print("Attempting to submit application")
            submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Submit application']")
            submit_button.click()
            time.sleep(random.uniform(1, constants.botSpeed))

            result = "* 🥳 Successfully applied to this job: " + str(offerPage)

        except Exception as e:
            print(f"Detailed error in application process: {str(e)}")
            result = f"* 🥵 Cannot apply to this Job! {str(offerPage)}"

        print(f"Application process result: {result}")
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
