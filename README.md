# err-reviewboard

Monitors Review Board for new review requests and displays them in your chat room

For more information about err you can find it here: [https://github.com/gbin/err](https://github.com/gbin/err)

## Installation and Configuration

### Dependencies

The following python packages are required to run this plugin:

 - simplejson

Installation:

    pip install simplejson

### config.py

Make sure you have all the required reviewboard settings in the err config.py

    RB_API_URL='http://uri-to-your-rb-install/api/'
    RB_USERNAME='yourusername'
    RB_PASSWORD='yourpassword'

### Intstallation

Make sure the plugin is in the `BOT_EXTRA_PLUGIN_DIR` path and it will get auto-discovered.

## Known issues

Currenly if the URI of your API is under a subdirectory ex (http://your-uri/reviewboard/api), the linking in the chat will not work correctly. The API endpoint that review board provides does not have a solid link to the review unless you make two queries to the API. Code just needs to be updated.
