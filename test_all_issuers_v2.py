# importing all needed libraries
import os
import re
import sys
from time import sleep
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import Select
import subprocess

# Test shop URLs
P2_BASE_URL = "https://ssl-liv-u6g-fo-acs-ve.wlp-acs.com/acs-protocol-2-test-service/"

# My sms URL (app used to recieve sms)
MY_SMS_URL = "https://app.mysms.com/#login"

ftnOTP='otp'
ftnpwd='qwer123'
# Path to text document containing card information
# Format in .txt file:
# card_PAN auth_method(otp/potp) password(optional, default=parole)
test_card_path = "C:\\Users\\w132292\\VisualCode\\selenium_test\\all_cards.txt"

# Path to test results (currently in same dir as the .py file)
test_result_path = "C:\\Users\\w132292\\VisualCode\\selenium_test\\Results"

# Path to BankId app desktop version
#bankIdAppPath = "C:\\Program Files (x86)\\BankID\\BankID.exe"

# Used in acs_information_confirmation_p1
# Checks for a line, that contains first element and compares lines result with second element
# ----------------------------------------------
# Example: veres_checklist[0] = ['<version>', '1.0.2']
# It will find line containing '<version>' and check if the text between <version></version> brackets contain '1.0.2'
# If only one element is given (pares_checklist[1]=['<date>']) it will find the line with <date> brackets and log the text between the brackets
# What shoukd be checked in protocol 1 test shop


# Used in acs_information_confirmation_p2

areq_checklist = [["acctNumber"], ["purchaseAmount", "29900"], ["purchaseDate"]]
ares_checklist = [
    ["messageVersion", "2.1.0"],
    ["authenticationType", "02"],
    ["acsChallengeMandated", "Y"],
    ["transStatus", "C"],
]
cres_checklist = [["transStatus", "Y"]]
rreq_checklist = [["authenticationMethod"], ["eci", "02"]]
rres_checklist = [["resultsStatus", "01"]]


# Chrome webdriver
def create_driver():
    global driver
    driver = webdriver.Chrome(
        executable_path=r"C:\\Users\\w132292\\VisualCode\\selenium_test\\Results"
    )
    driver.implicitly_wait(10)


# take screenshot - function
def take_screenshot(screenshot_reason, pan=""):
    driver.save_screenshot(
        test_result_path + "Screenshots\\" + screenshot_reason + pan + ".png"
    )
    pass


# for cration path where will be saved test results
def create_test_result_path():
    # Get the date and time of execution
    exe_time = datetime.now()
    time_string = exe_time.strftime("%d-%m-%Y-at-%H-%M")

    # Creates new folder in TestScreenshots with the template
    newpath = (
        "C:\\Users\\w132292\\VisualCode\\selenium_test\\chromeDriver\\chromeDriver.exe"
        + time_string
        + "\\"
    )
    if not os.path.exists(newpath):
        os.makedirs(newpath + "Screenshots")

    # Create test result text file
    with open(newpath + "test_results.txt", "w") as f:
        f.write(
            "Test execution started at "
            + exe_time.strftime("%d.%m.%Y at %H:%M:%S")
            + "\n"
        )

    # Makes a path to the new folder
    global test_result_path
    test_result_path = newpath
    pass


# function for adding results in text file
def new_log_entry(log_text):
    with open(test_result_path + "test_results.txt", "a") as f:
        f.write(log_text)
    pass


# function for opening new tab for mysms
def open_mysms():
    # Switch to the new tab
    driver.execute_script("window.open(" ");")
    driver.switch_to.window(driver.window_handles[1])
    driver.get(MY_SMS_URL)
    sleep(3)

    # Log In to mysms:
    zz_phone_number = "20202396"
    mysms_password = "world135Line"

    driver.find_element(By.LINK_TEXT, "Sign in with your mobile number").click()
    driver.find_element(By.CSS_SELECTOR, ".list").click()
    dropdown = driver.find_element(By.CSS_SELECTOR, ".list")
    dropdown.find_element(By.XPATH, '//option[. = "Latvia (+371)"]').click()
    driver.find_element("class name", "msisdn").send_keys(zz_phone_number)
    driver.find_element("class name", "html5TextBox").send_keys(mysms_password)
    driver.find_element(By.CSS_SELECTOR, ".login > div > div").click()
    sleep(5)

    pass


# function for getting OTP from mysms
def get_otp(card_pan):
    if driver.current_url != "https://app.mysms.com/":
        # Switch to mysms tab
        driver.switch_to.window(driver.window_handles[1])

    # Reload page
    sleep(2)
    driver.get("https://app.mysms.com/")
    sleep(3)
    take_screenshot("smsOpened", card_pan)
    try:
        # Get latest sms
        my_sms_str = driver.find_element(By.XPATH, "//span/span[2]").text
        otp_array = [int(s) for s in my_sms_str.split() if s.isdigit()]
        # Makes otp 6 symbols long (if the otp starts with zeros, they would get lost in transformation to integer)

        if (len(str(otp_array[0]))) < 6:
            otp = str(otp_array[1])
        else:
            otp = str(otp_array[0])

        driver.switch_to.window(driver.window_handles[0])
        return otp
    except Exception:
        take_screenshot("getOTP-Error", card_pan)
        new_log_entry(
            f"Something went wrong while getting otp, check {test_result_path}Screenshots\\getOTP-Error{card_pan}"
        )
        driver.switch_to.window(driver.window_handles[0])
        return -1


# check if test passed (compare actual result vs expected)
def check_protocol2_message_details(protocol_message, checklist):
    test_successful = True
    for line in protocol_message.splitlines():
        l = re.findall('"([^"]*)"', line)
        if len(l) > 1:
            for check in checklist:
                if check[0] in l[0]:
                    if len(check) > 1:
                        if l[1] == check[1]:
                            new_log_entry(str(check[0]) + " = " + l[1] + " = OK\n")
                        else:
                            new_log_entry(
                                str(check[0])
                                + " expected = "
                                + check[1]
                                + ". Result = "
                                + l[1]
                                + ". FAILED\n"
                            )
                            test_successful = False
                    else:
                        new_log_entry(str(check[0]) + " = " + l[1] + "\n")

    pass


def acs_information_confirmation_p2():
    sleep(3)

    try:
        acs_challenge_mandated = driver.find_element(
            By.XPATH, '//*[@id="acs-info-action"]/div/div[1]/div[1]/div'
        ).text

        cres_trans_status = driver.find_element(
            By.XPATH, '//*[@id="acs-info-action"]/div/div[1]/div[2]/div'
        ).text

        rreq_trans_status = driver.find_element(
            By.XPATH, '//*[@id="acs-info-action"]/div/div[1]/div[3]/div'
        ).text

        # Open protocol message details
        driver.find_element(By.XPATH, '//*[@id="protocol-messages-heading"]/h4').click()

        # Get ARes, CRes and RReq output
        areq_output = driver.find_element(
            By.XPATH, '//*[@id="protocol-messages-action"]/div/div[1]/pre'
        ).text

        ares_output = driver.find_element(
            By.XPATH, '//*[@id="protocol-messages-action"]/div/div[2]/pre'
        ).text

        cres_output = driver.find_element(
            By.XPATH, '//*[@id="protocol-messages-action"]/div/div[4]/pre'
        ).text

        rreq_output = driver.find_element(
            By.XPATH, '//*[@id="protocol-messages-action"]/div/div[5]/pre'
        ).text

        rres_output = driver.find_element(
            By.XPATH, '//*[@id="protocol-messages-action"]/div/div[6]/pre'
        ).text
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        check_protocol2_message_details(ares_output, ares_checklist)
        check_protocol2_message_details(cres_output, cres_checklist)
        check_protocol2_message_details(rreq_output, rreq_checklist)
        check_protocol2_message_details(rres_output, rres_checklist)

    except NoSuchElementException:
        new_log_entry("Element not found in acs information confirmation")

    pass


def test_successful_transaction_p2(
    transaction_method, card_pan, card_password="parole"
):
    new_log_entry(
        "-" * 30
        + "\nProtocol 2 transaction initialized with\nCard PAN: "
        + card_pan
        + "\nAuthentication method: "
        + transaction_method
        + "\nPassword: "
        + card_password
        + "\n\n"
    )
    # Switch to testshop tab
    if "wlp-acs" not in driver.current_url:
        driver.switch_to.window(driver.window_handles[0])
        sleep(1)
    # Start transaction

    sleep(3)
    search_input = driver.find_element(By.ID, "card-pan")
    search_input.send_keys(card_pan)
    sleep(5)

    driver.find_element(
        By.XPATH, "//select[@name='networkName']/option[text()='MASTERCARD']"
    ).click()  # select value Mastercard from dropdown

    driver.find_element(By.ID, "button1").click()
    sleep(10)
    take_screenshot("TransactionInitialised", card_pan)

    # Enter password:
    if transaction_method == "potp":
        sleep(3)
        driver.find_element(By.XPATH, "//div[@id='otp-form']/div/input").click()
        driver.find_element(By.XPATH, "//div[@id='otp-form']/div/input").send_keys(
            card_password
        )
        sleep(1)
        driver.find_element(
            By.XPATH, "//val-button[@id='validateButton']/button"
        ).click()
        sleep(1)
        take_screenshot("PasswordEntered", card_pan)
          # Enter otp:
        sleep(10)
        otp = get_otp(card_pan)
        if otp == -1:
            driver.get(P2_BASE_URL)
            pass
            
        driver.find_element(By.XPATH, "//div[@id='otp-form']/div/input").click()
        driver.find_element(By.XPATH, "//*[@id='otp-form']/div/input").send_keys(otp)
        sleep(1)
        driver.find_element(By.XPATH, "//val-button[@id='validateButton']/button").click()
        take_screenshot("otpEntered", card_pan)

        sleep(10)
        take_screenshot("transactionComplete", card_pan)
    if transaction_method == "digipass":
        sleep(3)
        driver.find_element(By.XPATH, "//div[@id='otp-form']/div/input").click()
        driver.find_element(By.XPATH, "//div[@id='otp-form']/div/input").send_keys(
            card_password
        )
        sleep(1)
        driver.find_element(
            By.XPATH, "//val-button[@id='validateButton']/button"
        ).click()
        sleep(1)
        take_screenshot("PasswordEntered", card_pan)
    if transaction_method == "ftn-openid":
        sleep(3)
        driver.find_element(
            By.XPATH, "//val-button[@id='validateButton']/button"
        ).click()
        take_screenshot("client_side", card_pan)
        sleep(5)
        driver.find_element(By.XPATH, "/html/body/div[1]/div/div/nav/ul/li[1]/a/div").click()
        sleep(3)
        driver.find_element(
            By.XPATH, "/html/body/div[1]/div/div/nav/form[1]/button"
        ).click()
        sleep(3)
  
        driver.find_element(
            By.XPATH, "//*[@id='Ssn']"
        ).click()
        sleep(3)

        driver.find_element(
            By.XPATH, "//*[@id='Ssn']"
        ).send_keys(card_password)
        sleep(3)
        driver.find_element(
            By.XPATH, "/html/body/div[1]/div/div/div/form/div/button"
        ).click()
        sleep(3)
        driver.switch_to.frame(driver.find_element(By.TAG_NAME,("iframe")))
        u = driver.find_element(By.XPATH,("//input[contains(@id,'_6')]"))
        u.click()
        u.send_keys("otp")
        sleep(3)
        driver.find_element(
            By.XPATH,
            "/html/body/div[3]/div/main/div/div[10]/div/form/div[2]/div[2]/button"
        ).click()
        sleep(3)
        driver.find_element(By.XPATH, "/html/body/div[3]/div/main/div/div[11]/div/form/div[2]/div[1]/div/div[2]/div/input").click()
        driver.find_element(By.XPATH, "/html/body/div[3]/div/main/div/div[11]/div/form/div[2]/div[1]/div/div[2]/div/input").send_keys("qwer1234")
        driver.find_element(
            By.XPATH,
            "/html/body/div[3]/div/main/div/div[11]/div/form/div[2]/div[2]/button"
        ).click()
        sleep(10)
        take_screenshot("transactionComplete", card_pan)
  
    if transaction_method == "nets_open_ID":
        sleep(3)
        driver.find_element(By.XPATH,("//*[@id='validateButton']/button")).click()
        take_screenshot("client_side", card_pan)
        driver.find_element(By.XPATH,("//*[@id='pki15']")).click()
        driver.switch_to.frame(driver.find_element(By.TAG_NAME,("iframe")))
        driver.find_element(By.XPATH,("/html/body/div[3]/div/main/div/div[14]/div/form/div[2]/div[1]/div/div[2]/div/input")).click()
        driver.find_element(By.XPATH,("/html/body/div[3]/div/main/div/div[14]/div/form/div[2]/div[1]/div/div[2]/div/input")).send_keys(card_password)
        driver.find_element(By.XPATH,("/html/body/div[3]/div/main/div/div[14]/div/form/div[2]/div[2]/button")).click()
        sleep(3)
        
        driver.find_element(By.XPATH, "/html/body/div[3]/div/main/div/div[10]/div/form/div[2]/div[1]/div/div[2]/div/input").click()
        driver.find_element(By.XPATH, "/html/body/div[3]/div/main/div/div[10]/div/form/div[2]/div[1]/div/div[2]/div/input").send_keys("otp")
        driver.find_element(By.XPATH,("/html/body/div[3]/div/main/div/div[10]/div/form/div[2]/div[2]/button")).click()
        sleep(3)
        driver.find_element(By.XPATH, "/html/body/div[3]/div/main/div/div[11]/div/form/div[2]/div[1]/div/div[2]/div/input").click()
        driver.find_element(By.XPATH, "/html/body/div[3]/div/main/div/div[11]/div/form/div[2]/div[1]/div/div[2]/div/input").send_keys("qwer1234")
        driver.find_element(By.XPATH,("/html/body/div[3]/div/main/div/div[11]/div/form/div[2]/div[2]/button")).click()
        sleep(10)
        take_screenshot("transactionComplete", card_pan)       
    if transaction_method == "bank_id":
        driver.find_element(By.XPATH,("//*[@id='validateButton']/button")).click()
        take_screenshot("client_side", card_pan)
        subprocess.call(bankIdAppPath)
    

    acs_information_confirmation_p2()
    pass


def test_all_cards(base_url):
    # Open test-shop
    create_driver()
    driver.get(base_url)
    driver.maximize_window()
    driver.implicitly_wait(10)
    sleep(3)
    take_screenshot("OpenTestshop", "")

    open_mysms()
    take_screenshot("OpenMysms", "")

    # Get test authentication information from file with line format: "PAN auth_method password"
    with open(test_card_path) as f:
        test_card_list = f.readlines()

    chrome_reset_needed = False

    # Run successful transaction tests with every card
    for card in test_card_list:
        temp = card.split()
        pan = temp[0]
        method = temp[1]
        try:
            if chrome_reset_needed:
                chrome_reset_needed = False
                # Opens everything needed for next test
                create_driver()
                driver.get(base_url)
                driver.implicitly_wait(10)
                sleep(3)
                open_mysms()
                sleep(1)
            # Checks input data and what protocol to test
            if len(temp) > 2:
                test_card_password = temp[2]
                test_successful_transaction_p2(method, pan, test_card_password)
                driver.get(base_url)
            else:
                test_successful_transaction_p2(method, pan)

        except NoSuchElementException:
            # Assesses, that some element wanst found and it was impossible to continue test
            new_log_entry(
                "Some element was missing, check screenshot at: "
                + test_result_path
                + "NoSuchElementException"
                + pan
                + " for more information\n"
            )
            take_screenshot("NoSuchElementException", pan)

            # Closes current chromedriver and tells, that to continue with next test case a new chrome setup is needed
            driver.quit()
            chrome_reset_needed = True
    driver.quit()
    pass


def test_transaction_cancellation_p2(
    transaction_method, card_pan, card_password="parole"
):
    new_log_entry(
        "-" * 30
        + "\nProtocol 2 transaction initialized with\nCard PAN: "
        + card_pan
        + "\nAuthentication method: "
        + transaction_method
        + "\nPassword: "
        + card_password
        + "\n\n"
    )
    # Switch to testshop tab
    if "wlp-acs" not in driver.current_url:
        driver.switch_to.window(driver.window_handles[0])
        sleep(1)
    # Start transaction

    sleep(3)
    search_input = driver.find_element(By.ID, "card-pan")
    search_input.send_keys(card_pan)
    driver.find_element(By.ID, "button1").click()
    sleep(10)
    take_screenshot("TransactionInitialised", card_pan)

    # Enter password:
    if transaction_method == "potp":
        sleep(3)
        driver.find_element(By.XPATH, "//div[@id='otp-form']/div/input").click()
        driver.find_element(By.XPATH, "//div[@id='otp-form']/div/input").send_keys(
            card_password
        )
        sleep(1)
        driver.find_element(
            By.XPATH, "//val-button[@id='validateButton']/button"
        ).click()
        sleep(1)
        take_screenshot("PasswordEntered", card_pan)

    # Enter otp:
    sleep(10)
    otp = get_otp(card_pan)
    if otp == -1:
        driver.get(P2_BASE_URL)
        pass
    driver.find_element(By.XPATH, "//div[@id='otp-form']/div/input").click()
    driver.find_element(By.XPATH, "//*[@id='otp-form']/div/input").send_keys(otp)
    sleep(1)
    driver.find_element(By.XPATH, "//val-button[@id='validateButton']/button").click()
    take_screenshot("otpEntered", card_pan)

    sleep(10)
    take_screenshot("transactionComplete", card_pan)
    acs_information_confirmation_p2()
    pass


def transaction_cancellation_p2(transaction_method, card_pan, card_password="parole"):
    new_log_entry(
        "-" * 30
        + "\nProtocol 2 transaction initialized with\nCard PAN: "
        + card_pan
        + "\nAuthentication method: "
        + transaction_method
        + "\n\n"
    )
    # Switch to testshop tab
    if "wlp-acs" not in driver.current_url:
        driver.switch_to.window(driver.window_handles[0])
        sleep(1)
    # Start transaction

    sleep(3)
    search_input = driver.find_element(By.ID, "card-pan")
    search_input.send_keys(card_pan)
    driver.find_element(By.ID, "button1").click()
    sleep(10)
    take_screenshot("TransactionInitialised", card_pan)
    driver.find_element(By.ID, "cancelButton").click()
    take_screenshot("TransactionCancellation", card_pan)
    driver.find_element(By.ID, "cancelButton").click()
    sleep(10)
    take_screenshot("TransactionCancellationResult", card_pan)


def test_all_cards_cancellation(base_url):
    # Open test-shop
    create_driver()
    driver.get(base_url)
    driver.maximize_window()
    driver.implicitly_wait(10)
    sleep(3)
    take_screenshot("OpenTestshop", "")

    # Get test authentication information from file with line format: "PAN auth_method password"
    with open(test_card_path) as f:
        test_card_list = f.readlines()

    chrome_reset_needed = False

    # Run successful transaction tests with every card
    for card in test_card_list:
        temp = card.split()
        pan = temp[0]
        method = temp[1]
        try:
            if chrome_reset_needed:
                chrome_reset_needed = False
                # Opens everything needed for next test
                create_driver()
                driver.get(base_url)
                driver.implicitly_wait(10)
                sleep(3)
                open_mysms()
                sleep(1)
            # Checks input data and what protocol to test
            if len(temp) > 2:
                test_card_password = temp[2]
                transaction_cancellation_p2(method, pan, test_card_password)
                driver.get(base_url)
            else:
                transaction_cancellation_p2(method, pan)

        except NoSuchElementException:
            # Assesses, that some element wanst found and it was impossible to continue test
            new_log_entry(
                "Some element was missing, check screenshot at: "
                + test_result_path
                + "NoSuchElementException"
                + pan
                + " for more information\n"
            )
            take_screenshot("NoSuchElementException", pan)

            # Closes current chromedriver and tells, that to continue with next test case a new chrome setup is needed
            driver.quit()
            chrome_reset_needed = True
    driver.quit()
    pass


def main():
    create_test_result_path()
    # test_all_cards_cancellation(P2_BASE_URL)
    test_all_cards(P2_BASE_URL)
    pass


if __name__ == "__main__":
    main()
