import fetch
import fudge
import pytest

# I am using pytest-mocker to doing the tests
# this is why I can do the (mocker) param and
# just get all the mock.Magic stuff.

#Working example without Fudge using pytest-mock
def test_getYamlData_nonExistantYamlFile(mocker):
    fake_sys = mocker.patch('sys.exit', autospec=True)
    fetch.getYamlConfigData("nonExistantFile")
    assert fake_sys.call_count == 1

def test_grabYamlData_missingData(mocker):
    mocker.patch('builtins.open', mocker.mock_open())
    mocker.patch('yaml.load', return_value={'walletID': '1'})
    fake_sys = mocker.patch('sys.exit', autospec=True)

    fetch.getYamlConfigData("fake_config.yaml")
    assert fake_sys.call_count == 1

def test_grabYamlConfigData_success(mocker):
    mocker.patch('builtins.open', mocker.mock_open())
    mocker.patch('yaml.load', return_value={'walletID': 'asdf', 'currencyCode': 'U'})

    rsp = fetch.getYamlConfigData('fake_config.yaml')
    assert rsp['walletID'] == "asdf"

def test_getMinerStats_noWalletID():
    call = fetch.getMinerStats()
    assert isinstance(call, tuple)
    assert call[0] is False

def test_getMinerStats_success(mocker):
    http_rsp = mocker.MagicMock()
    http_rsp.status_code = 200
    http_rsp.json.return_value = {'Some': 'Thing'}

    mocker.patch('requests.get').return_value = http_rsp

    call = fetch.getMinerStats("WalletID")
    assert isinstance(call, tuple)
    assert call[0]
    assert call[1] == {'Some': 'Thing'}

def test_getMinerStats_success_web_failure(mocker):
    http_rsp = mocker.MagicMock()
    http_rsp.status_code = 550
    mocker.patch('requests.get').return_value = http_rsp

    call = fetch.getMinerStats("asdf")
    assert isinstance(call, tuple)
    assert call[0] is False
    assert isinstance(call[1], str)

def test_returned_makeHumanReadable_nonVerbose_success():
    miner = {
        "stats": {
          "balance": "8",
          "hashes": "5",
          "hashrate": "1.93 KH",
          "lastShare": "1",
          "paid": "9"},
        "charts": {
            "hashrate": [[1,1,1],[2,2,2]]}
        }
    ticker = '0.01 USD/XMR'
    expected = "Balance: 0.000000000008 XMR\nCurHash: 1.93 KH\nHashAvg: 1.5 H/s\nCurrent Market: 0.01 USD/XMR"

    hr = fetch.makeHumanReadable(miner, ticker)
    assert isinstance(hr, str)
    assert hr == expected

def test_returned_makeHumanReadable_verbose_success():
    miner = {
        "stats": {
          "balance": "8",
          "hashes": "5",
          "hashrate": "1.93 KH",
          "lastShare": "1",
          "paid": "9"},
        "charts": {
            "hashrate": [[1,1,1],[2,2,2]]}
        }
    expected = "<strong>Current XMR Balance:</strong> 0.000000000008 XMR<br/><strong>Current Hashrate:</strong> 1.93 KH<br/><strong>Average Hash Rate:</strong> 1.5 H/s<br/><strong>Current Market:</strong> 0.01 USD/XMR"
    ticker = '0.01 USD/XMR'

    hr = fetch.makeHumanReadable(miner, ticker, True)
    assert isinstance(hr, str)
    assert hr == expected

def test_getCurrencyConversion_web_failure(mocker):
    http_rsp = mocker.MagicMock()
    http_rsp.status_code = 500
    mocker.patch('requests.get').return_value = http_rsp

    call = fetch.getCurrencyConversion('asdf') 
    assert isinstance(call, tuple)
    assert call[0] is False
    assert isinstance(call[1], str)

def test_getCurrencyConversion_fail_format_change(mocker):
    web_response = {'ticker': {'something': 1}}
    http_rsp = mocker.MagicMock()
    http_rsp.status_code = 200
    http_rsp.json.return_value = web_response
    mocker.patch('requests.get').return_value = http_rsp

    call = fetch.getCurrencyConversion('USD')
    assert isinstance(call, tuple)
    assert call[0] is False
    assert isinstance(call[1], str)

def test_getCurrencyConversion_success(mocker):
    web_response = {'ticker': {'price': '0.01'}}
    http_rsp = mocker.MagicMock()
    http_rsp.status_code = 200
    http_rsp.json.return_value = web_response
    mocker.patch('requests.get').return_value = http_rsp

    call = fetch.getCurrencyConversion('KOR')
    assert isinstance(call, tuple)
    assert call[0]
    assert isinstance(call[1], str)
    assert call[1] == "0.01 KOR/XMR"

def test_makeFloatHumanReadable():
    assert fetch.makeFloatHumanReadable(129295127106) == '0.129295127106'
    assert fetch.makeFloatHumanReadable(12929512710600) == '12.929512710600'
    assert fetch.makeFloatHumanReadable(129295127) == '0.000129295127'

def test_buildSGAttachment_success(mocker):
    from sendgrid.helpers.mail import Attachment
    mocker.patch("sendgrid.helpers.mail.Attachment", create=True)

    atch = fetch.build_sg_attachment("asdf", "qwer")
    assert atch.content == 'asdf'
    assert atch.type == 'image/png'
    assert atch.filename == 'graph.png'
    assert atch.disposition == 'inline'
    assert atch.content_id == 'qwer'

