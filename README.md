# Bellbird notifications

Bellbird sends marketplace notifications over push, email, SMS and in-app. This lab runs an API, a Redis-backed queue, one worker, and a fake provider whose latency and failures you can change while everything is running.

## Run

You need Docker with Compose. `make up` starts it all and `make test` runs the checks. The API is on `http://localhost:58002` and the provider's control API on `http://localhost:58001`. `make down` removes the local volume.

## Load and break it

`make notify` queues fifteen email newsletters, then one urgent push carrying a login code, waits for delivery and prints the metrics:

```
{"delivered": N, "lost": N, "queue_depth": N, "dlq": N, "provider_calls": N, "otp_p95_ms": N}
```

`make metrics` prints the same counters at any time. `otp_p95_ms` is the p95 delivery time of push notifications.

The provider's `POST /_control` takes `{"latency_ms": 250}` or `{"fail": true}`. `make provider-outage` sends the second one; send `{"fail": false}` to bring it back.

The queue and the delivery records both live in Redis.

## License

MIT. See `LICENSE`.
