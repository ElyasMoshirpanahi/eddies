# middleware function template

This Repo is an Azure function acting as middleware, forwarding requests between fronted
and backend. It accepts CORS requests.

# Getting started



1. Get your azure function's publish profile credentials:
 - If you are using Azure's normal consumption plan: 
   1. Go to the setting of your repositiory and add that information as  secret key called `AZURE_FUNCTIONAPP_PUBLISH_PROFILE` <br>
  ![azure](https://github.com/zaubar/middlware-template/assets/37846222/61cafe18-d9fe-423d-a45d-19379804772a)
  <br><br>
 - If you are using Azure's flex consumption plan: 
   1. You need to get your AZURE_CREDENTIALS via azure cli locally and then add it as a secret key called `AZURE_CREDENTIALS`

2.  Push your function code to github, it will then be automatically deployed to the azure function portal

3.  Go to the Function App resource, and select `Configuration` on the left-hand side
    bar. Add the following variables:

    1. `Environment variable` to set secret variables if needed

4.  Go to the Function App resource, and select `Functions` on the left-hand side
    bar, and then `middleware`. In `Code + Test`, select `Get function URL`. This will give
    the Azure fn endpoint url and auth code.

5.  Set CORS settings by going to the Function App resource, and select `CORS` on the
    left-hand side bar and change the default host to `*`.

# Test request

You can test that the Azure function is working as expected by running this example
code:

```python
"""Test request to azure function middleware"""
import io
import json

import requests

middleware_url = "https://yourfunctionurl.com"


if __name__ == "__main__":
    """Main entry script"""
    params = {
        "image": open("input_image.jpg", "rb").read(),
		"prompt":"a detailed image"
    }

    # perform the request
    result = requests.post(middleware_url, files=params)

    if result.status_code == 200:
        output_bytes = io.BytesIO(result.content).getvalue()

        with open("output_azurefn_magic_img.png", "wb") as output_file:
            output_file.write(output_bytes)

        print("Success")
    else:
        print(f"Error: {result.reason} - {result.text}")
```
# eddies
