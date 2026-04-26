# lastboard

## setup/hosting notes

The following is specific to me and might not be relevant to you if you ever 
decide to host this for some reason.

- Uses mise (and uv via mise) for environment configuration, but ultimately just needs a python 3.13.* environment
- Required env setup detailed in `.env.example`
- Generated application instance data (e.g. database files, temporary session files, etc) are stored in /data and not checked into source
