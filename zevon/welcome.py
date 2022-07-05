welcome_html = '''<html>
    <head>
        <title>Lambda Tool v{version}
    </head>
    <body>
        <div>
            <h3><a
                target="giithoob"
                href="https://github.com/muckamuck/lambda-tool/blob/master/README.md">Lambda
                Tool v{version}</a>:
            </h3>
            <p>A tool to create and deploy Lambda Functions to AWS (for python things).</p>
            <ul>
                <li>Create a new Python AWS Lambda from included template. Either a simple lambda function or a Flask based microservice.</li>
                <li>Deploy AWS Lambda created with this tool. It generates a CloudFormation file and creates a stack from that template.</li>
                <li>Optionally, integrate the new lambda with an AWS API Gateway, i.e. make a Flask application</li>
                <li>Optionally, subscribe the new lambda to an SNS topic</li>
                <li>Optionally, trust an arbitrary AWS service like cognito or S3</li>
            </ul>
        </div>
        <div>
            Zevon version: 0.2.2
        </div>
    </body>
</html>'''
