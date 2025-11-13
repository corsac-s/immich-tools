# Set of tools to interact with Immich photo software

## Origins / immich-stack

This is heavily based on the
[immich-stack](https://github.com/sid3windr/immich-stack) project by Tom
Laermans. The [stack](stack.py) tool was edited to tune the stacking criteria
to fit my needs. 
## Requirements

* Python 3
* An [Immich](https://immich.app) account
* An API key for your account

## Creating an API key

* Click on your profile icon in the top right, then choose **Account Settings**.
* Fold out **API Keys** and click **New API Key**.
* Give it a useful name, like **immich-stack**.
* Give it **duplicate.read** and **stack.create** permissions .
* Click **Create**. You'll be presented with a single chance to copy this API
key to your clipboard. Put it in your INI file (see below) and/or your
password manager.

## Configuration

### INI configuration

The script reads `immich.ini` in the same directory as the script.

```
[immich]
url=https://immich.example.com
api_key=f9c899b3bef7fbe7c77729099c1463e5
```

The `immich` section requires your Immich instance's URL, and the API key as
created above.

### Environment variables

The script can also use environment variables instead of the INI file.
If the INI value is set, it will take precedence over the environment
variables.

Immich environment variable names are `IMMICH_URL` and `IMMICH_API_KEY`.

## Stack

For some reasons I have multiple time the same file (same basename, same
extensions) on different part of the filesystem, and I need to stack them in
immich. With this tool I can automatically identify and stack them.

To just show what would be stacked, without actually
stacking, use the dry run option:

```
./stack.py --dry-run
```

To stack your identically named duplicates, just run:

```
./stack.py --stack
```

While the script only has one function, I didn't want to start messing with
your Immich instance if you ran it without parameters.
