# handling the serverless imports
# needed for the serverless-python-requirements
# for the serverless deployment.
try:
    import unzip_requirements
except ImportError:
    pass

import base64
import io
import sys
import logging
from datetime import datetime as dt
from functools import reduce

# external Libraries
from matplotlib import rcParams
from sendgrid.helpers.mail import Email, Content, Mail, Attachment
from twilio.rest import Client
import yaml
import requests
import sendgrid
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

logging.basicConfig(
    level=logging.INFO)
logger = logging.getLogger('logger')
ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s :: %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

def buildImage(data):
    rcParams['font.family'] = 'sans-serif'
    rcParams['font.sans-serif'] = ['DejaVu Sans']

    hashrates = []
    dates = []

    #Get hashrates from the info
    hashrates.extend(list(map(lambda x: x[1], data['charts']['hashrate'])))
    dates.extend(list(map(lambda x: dt.fromtimestamp(x[0]), data['charts']['hashrate'])))

    fig = plt.figure()
    # Set a more reasonable size of our figure
    fig.set_figwidth(6)
    fig.set_figheight(2.4)

    # This is adjusts for the Labels
    plt.gcf().subplots_adjust(bottom=0.4)
    plt.gcf().subplots_adjust(left=0.2)
    ax = fig.add_subplot(111)

    # Remove the lines on the top and right of the plot
    ax.spines['right'].set_color('none')
    ax.spines['top'].set_color('none')

    # Set axis Labels
    ax.set(xlabel='Date', ylabel='Hashrates')

    # Fill the plot
    ax.fill_between(dates, hashrates, color='#ffa163')
    ax.plot(dates, hashrates, color='#999999', lw=3)

    # Locators help us space our labels appropriately.
    # https://matplotlib.org/api/dates_api.html#matplotlib.dates.AutoDateFormatter
    locator = mdates.AutoDateLocator()
    formatter = mdates.AutoDateFormatter(locator)
    formatter.scaled[1/(24.)] = '%a %k:%M' # only show min and sec

    # Format the x axis ticks
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    # Format the Y axis ticks
    formatter = ticker.FormatStrFormatter('%i H/s')
    ax.yaxis.set_major_formatter(formatter)
    # Set the range to remove padding
    ax.set_ylim((0, ax.get_ylim()[1]))
    ax.set_xlim((dates[0], dates[-1]))

    # Set lables for the major x axis ticks
    for tick in ax.yaxis.get_major_ticks():
        tick.label1On = True

    # Rotate the labels for readability
    for tick in ax.get_xticklabels():
        tick.set_rotation(20)

    #Output a PNG image of our graph as a string
    output = io.BytesIO()
    plt.savefig(output, format="png", transparent=True)
    asdf = base64.b64encode(output.getvalue())
    return asdf.decode("utf-8")

def getYamlConfigData(filename=''):
    try:
        with open(filename, 'r') as yamlInput:
            data = yaml.load(yamlInput)
            wid = data.get('walletID', False)
            cc = data.get('currencyCode', False)
            if wid and cc:
                return data
            else:
                logging.critical("Missing walletID or currencyCode in config file.")
                sys.exit(1)
    except IOError:
        logging.critical("Missing Config.yaml file. Cannot Continue. {0}".format(filename))
        sys.exit(1)

def makeFloatHumanReadable(mantissa):
    # make floting points human readable from API
    mantissa_len = 12
    mantissa_delta = len(str(mantissa))-mantissa_len
    if mantissa_delta == 0:
        return "0.{0}".format(mantissa)
    elif mantissa_delta > 0:
        return "{0}.{1}".format(
            str(mantissa)[:mantissa_delta],
            str(mantissa)[mantissa_delta:])
    else:
        return "0.{0}{1}".format(''.zfill(mantissa_delta*-1), mantissa)

def calc_avg_hashrate(data):
    hashrates = list(map(lambda x: x[1], data['charts']["hashrate"]))
    return reduce(lambda x, y: float(x) + y, hashrates) / len(hashrates)

def getMinerStats(walletID=None):
    ''' getMinerStats calls monerohash.com and returns
        a tuple with the status of the call and either
        an error or the data you want. 

        :param walletID: the string of you wallet ID
        :return: tuple (Boolean, Data)
        '''
    if walletID:
        params = {'address': walletID}
        url = 'https://monerohash.com/api/stats_address'

        rsp = requests.get(url, params=params)
        if rsp.status_code == 200:
            return (True, rsp.json())
        return (False, "There was a failure in the call")
    else:
        return (False, "You are a Dummy, I can't look up nothing")

def getCurrencyConversion(cur_code):
    rsp = requests.get("https://api.cryptonator.com/api/ticker/xmr-{0}".format(cur_code.lower()))
    if rsp.status_code == 200:
        rspj = rsp.json()
        if rspj.get('ticker', False) and rspj['ticker'].get('price', False):
            return (True, "{0} {1}/XMR".format(float(rspj['ticker']['price']), cur_code))
        else:
            return (False, "Web API Format Changed, Parsing Error.")
    else: 
        return (False, "Web Call Failure, Site unreachable.")

def makeHumanReadable(miningData, tickerData, verbose=False):
    TRUNCATE_FLOATS_TO = 3
    if verbose:
        if tickerData and miningData.get('stats'):
            sts = miningData['stats']
            hashrate = sts.get('hashrate', '0 H')
            if sts.get('balance', False) and sts.get('paid', False):
                avg_hash = calc_avg_hashrate(miningData)
                return "<strong>Current XMR Balance:</strong> {0} XMR<br/>" \
                       "<strong>Current Hashrate:</strong> {1}<br/>" \
                       "<strong>Average Hash Rate:</strong> {2} H/s<br/>" \
                       "<strong>Current Market:</strong> {3}".format(
                               makeFloatHumanReadable(sts['balance']),
                               hashrate,
                               round(avg_hash, TRUNCATE_FLOATS_TO),
                               tickerData)
    else:
        if tickerData and miningData.get('stats'):
            sts = miningData['stats']
            hashrate = sts.get('hashrate', '0 H')
            if sts.get('balance', False) and sts.get('paid', False):
                avg_hash = calc_avg_hashrate(miningData)
                return "Balance: {0} XMR\n" \
                       "CurHash: {1}\n" \
                       "HashAvg: {2} H/s\n" \
                       "Current Market: {3}".format(
                               makeFloatHumanReadable(sts['balance']),
                               hashrate,
                               round(avg_hash, TRUNCATE_FLOATS_TO),
                               tickerData)

def build_sg_attachment(file_base64, content_id):
    '''Creates an attachment for an email and sets
       the content-id for inline display '''
    attachment = Attachment()
    attachment.content = (file_base64)
    attachment.type = "image/png"
    attachment.filename = "graph.png"
    attachment.disposition = "inline"
    attachment.content_id = content_id
    return attachment

def sendEmail(inputs, message, with_image=True, data=None):
    sg = sendgrid.SendGridAPIClient(apikey=inputs['sendgridAPIKey'])
    from_email = Email(inputs.get('sendgridEmail'))
    to_email = Email(inputs.get('destinationEmail'))
    subject = "MoneroHash Results for {0}".format(dt.utcnow().strftime("%d/%m/%y"))

    if with_image:
        file_base64 = buildImage(data)
        content_id = "monerograph"
        attachment = build_sg_attachment(file_base64, content_id)
        message = '<img alt="Hashrate Chart" src="cid:{0}" ></img><br/>{1}'.format(content_id, message)
        content = Content("text/html", message)
        mail = Mail(from_email, subject, to_email, content)
        mail.add_attachment(attachment)
    else:
        content = Content("text/html", message)
        mail = Mail(from_email, subject, to_email, content)

    rsp = sg.client.mail.send.post(request_body=mail.get())
    print(rsp)

    if str(rsp.status_code)[0] == '2':
        return True
    else:
        return False

def sendSMS(inputs, message):
    twilioAccount = inputs['twilioAccount']
    toPhone = inputs['destinationPhone']
    fromPhone = inputs['twilioPhone']
    twilioAPIKEY = inputs['twilioAPIKey']
    twilioClient = Client(twilioAccount, twilioAPIKEY)

    message = twilioClient.messages.create(to=toPhone, from_=fromPhone, body=message)
    if message.error_code is None:
        return True
    else:
        return False

def run(event, context):
    errors = []
    inputs = getYamlConfigData('config.yaml')
    walletID = inputs['walletID']

    if inputs.get('serverLogs', False):
        log_name = 'MoneroHash-booper.txt'
        if inputs.get('serverLogDirectory', False) != '':
            log_name = "{0}{1}".format(inputs['serverLogDirectory'], log_name)
        logger = logging.getLogger('logger')
        fh = logging.FileHandler(filename='monerohash-booper-log.txt')
        formatter = logging.Formatter('%(asctime)s :: %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        logger.setLevel(inputs['serverLogLevel'])

    logger.info("Fetching Miner Data")
    miningData = getMinerStats(walletID)[1]

    logger.info("Fetching XMR Price")
    tickerData = getCurrencyConversion(inputs['currencyCode'])[1]
    logger.info("Success")

    if inputs.get('twilioAPIKey', False) != '':
        logger.debug("TwilioAPIKey found attempting sms send")
        humanReadable = makeHumanReadable(miningData, tickerData)
        logger.info("Sending SMS")
        if sendSMS(inputs, humanReadable):
            logger.info("Success")
        else:
            logger.info("Failure")

    if inputs.get('sendgridAPIKey', False) != '':
        logger.debug("sendgridAPIKey found attempting email send")
        humanReadable = makeHumanReadable(miningData, tickerData, True)
        logger.info("Sending Email")
        if sendEmail(inputs, humanReadable, (lambda x: x.lower() == 'true')(inputs.get("emailWithImage", 'true')), miningData):
            logger.info("Success")
        else:
            logger.info("Failure")

    logger.info("Report:\n\n{0}\n".format(
        makeHumanReadable(miningData, tickerData)))

if __name__ == "__main__":
    run('', '')

