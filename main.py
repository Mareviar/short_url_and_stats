from flask import Flask, redirect, request, jsonify
import subprocess


app = Flask(__name__)

hostname = "192.168.0.16"
databaseHost = '127.0.0.1'


def askDB(command, name,arg1, arg2):
    answer = subprocess.Popen(['C:\\Users\\Huawei_\\PycharmProjects\\flaskProject\\MDB.exe', databaseHost, command, name, arg1, arg2], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return str(answer.communicate()[0].strip())[2:-1]


@app.route("/")
def hello():
    return 'It is a statistic service, make a POST-request'

@app.route("/", methods = ['POST'])
def register():
    ip = request.form.get('ip')
    shortURL = request.form.get('shortURL')
    longURL = request.form.get('longURL')
    time = request.form.get('time')

    countStr = askDB('HGET', 'parameters', 'count', '')
    if countStr == 'Error':
        askDB('HSET', 'parameters', 'count', '0')
        countStr = '0'
    count = int(countStr)
    askDB('HSET', 'parameters', 'count', str(count+1))

    askDB('HSET', 'URLs', str(count), longURL+ '('+shortURL +')')
    askDB('HSET', 'IPs', str(count), ip)
    askDB('HSET', 'TIMEs', str(count), time)

    return "Saved"

class Dimension():
    def addDimension(self, report):
        pass

class ParentDimension(Dimension):
    def __init__(self, metrick, maxID, value):
        self.metrick = metrick
        self.maxID = maxID
        self.value = value

    def addDimension(self, report):
        for j in range(self.maxID):
            if report[j][self.metrick] == self.value:
                Pid = int(report[j]['Id']) #j
                report[j]['Count'] += 1
                break
        else:
            report.append({"Id": self.maxID, "Pid": None, "URL": None,"SourceIP": None, "TimeInterval": None, "Count": 1})
            report[self.maxID][self.metrick] = self.value
            Pid = int(report[self.maxID]['Id'])
            self.maxID+=1
        return [Pid, self.maxID]

class ChildrenDimension(Dimension):
    def __init__(self, metrick, maxID, value, Pid):
        self.metrick = metrick
        self.maxID = maxID
        self.value = value
        self.Pid = Pid
    def addDimension(self, report):
        for j in range(self.maxID):
            if report[j][self.metrick] == self.value and report[j]["Pid"] == self.Pid:
                Pid = int(report[j]['Id'])
                report[j]['Count'] += 1
                break
        else:
            report.append({"Id": self.maxID, "Pid": None, "URL": None,"SourceIP": None, "TimeInterval": None, "Count": 1})
            report[self.maxID][self.metrick] = self.value
            report[self.maxID]["Pid"] = int(self.Pid)
            Pid = int(report[self.maxID]['Id'])
            self.maxID+=1
        return [Pid, self.maxID]

@app.route("/report", methods = ['POST'])
def makeReport():
    request_data = request.get_json()
    first = request_data["Dimensions"][0]
    report = []
    maxID = 0
    Pid = -1
    countReports = int(askDB('HGET', 'parameters', 'count', ''))
    for i in range(countReports):
        singleLogin = {}
        singleLogin['URL'] = askDB('HGET', 'URLs', str(i), '')
        singleLogin['SourceIP'] = askDB('HGET', 'IPs', str(i), '')
        singleLogin['TimeInterval'] = askDB('HGET', 'TIMEs', str(i), '')

        element = ParentDimension(first, maxID, singleLogin[first])

        result = element.addDimension(report)
        Pid=result[0]
        maxID = result[1]
        for j in range(len(request_data["Dimensions"])-1):
            element = ChildrenDimension(request_data["Dimensions"][j+1], maxID, singleLogin[request_data["Dimensions"][j+1]], Pid)
            result = element.addDimension(report)
            Pid = result[0]
            maxID = result[1]

    return jsonify(report)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8001)