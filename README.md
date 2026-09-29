# Bellbird notifications

Bellbird sends marketplace notifications over push, email, SMS and in-app.
The service accepts them over HTTP, queues them in Redis, and a worker hands
each one to the delivery provider.

```
service/    the notification service: Python and FastAPI, API and worker in one container
harness/    Redis, the fake provider, and the tools the drills use
contract/   black-box tests of what the service answers
```

## Run

You need Docker with Compose, nothing else. `make up` starts the service,
Redis and the provider. The service is on `http://localhost:58002`, the
provider on `http://localhost:58001`. `make contract` runs the contract
tests; `make down` removes everything.

`POST /notifications` takes `{"channel": "email", "body": "hello"}`, plus
`user_id` and `urgency` (`urgent`, `normal` or `low`), and answers 202 with
an id. `GET /notifications/{id}` shows its status.

## Load and break it

- `make notify` sends fifteen low-urgency email newsletters, then one urgent
  push carrying a login code, waits until the provider has all sixteen, and
  prints:

  ```
  sent=16 delivered=N otp_position=N otp_ms=N
  ```

  `otp_position` is where the code landed among the sixteen deliveries, and
  `otp_ms` how long it took from being accepted to reaching the provider.
- `make outage` takes the provider down, sends five notifications, and
  brings it back two seconds later; `make outage-long` keeps it down for ten.
  Both wait up to 90 seconds and print:

  ```
  accepted=5 delivered=N dead_lettered=N lost=N
  ```

  A notification counts as `dead_lettered` when `GET /notifications/{id}`
  reports that status; one the provider never got, in any other status, is
  `lost`.
- `make provider-down`, `make provider-up` and `make provider-slow` (250 ms
  per send instead of 40) change the provider by hand. `make received` lists
  what it has accepted.

## Porting the service

The service is Python and FastAPI; you can write it in another language. It
listens on port 8000 inside its container, reads `REDIS_URL` and
`PROVIDER_URL`, sends each notification with `POST {PROVIDER_URL}/send`
(a JSON body with at least `id`, `user_id`, `channel`, `body` and `urgency`),
and answers the routes in `contract/openapi.yaml`. Build it from
`service/Dockerfile`, then run `make contract` until it passes.

## License

MIT. See `LICENSE`.
