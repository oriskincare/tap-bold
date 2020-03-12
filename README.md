# tap-bold

This is a [Singer](https://singer.io) tap that produces JSON-formatted data
following the [Singer
spec](https://github.com/singer-io/getting-started/blob/master/SPEC.md).

This tap:

- Pulls raw data from [Bold Recurring Orders API](http://boldapps.net)
- Extracts the following resources:
  - [Subscriptions](https://docs.boldapps.net/subscriptions/integration/index.html#subscriptions)
- Outputs the schema for the resource (TODO: missing a few fields)
- Replicates the whole resource since Bold doesn't allow queries by last_updated