# Up for Home Assistant

**Up Banking** is a small, read-only Home Assistant custom integration for the [Up Banking API](https://developer.up.com.au/). It is designed for balances in dashboards and transaction activity in automations; Up remains the source of truth for accounts, categories, budgets, and history.

## What it provides

- One $ balance sensor for each account selected during setup, including Savers and 2Up (joint) accounts.
- Stable entity identity based on Up's account ID, so changing an account name does not create a new entity.
- The `up_banking_transaction` Home Assistant event for new activity. Its compact data includes `transaction_id`, `event_type` (`created`, `settled`, or `deleted`), `status` (`held`, `settled`, or `deleted`), `account_id`, `amount`, `currency`, `description`, and `created_at`.
- A five-minute coordinated poll. It reads changed activity since the last successful poll, so a Home Assistant restart or brief outage catches up. It retains at most 500 small de-duplication records in HA storage and does **not** put transaction history on entities or into Recorder attributes.

## Install with HACS

1. In HACS, open the three-dot menu, choose **Custom repositories**, then add `https://git.napper.au/napper/up-ha` as an **Integration**.
2. Search for **Up Banking**, install it, then restart Home Assistant.
3. Go to **Settings → Devices & services → Add integration**, select **Up Banking**, and enter an Up personal access token from the [Up developer portal](https://developer.up.com.au/).
4. Select the accounts to expose. Open the integration's **Configure** option later to change that selection.

The token is held in Home Assistant's config-entry storage; this integration deliberately never logs it. Do not paste it into YAML, automations, issues, or chat.

For a manual install, copy `custom_components/up_banking` into `/config/custom_components/`, restart Home Assistant, then follow steps 3–4.

## Automation example

```yaml
automation:
  - alias: Tell me about newly held purchases
    triggers:
      - trigger: event
        event_type: up_banking_transaction
        event_data:
          event_type: created
          status: held
    actions:
      - action: notify.mobile_app_phone
        data:
          message: >-
            {{ trigger.event.data.description }}:
            {{ trigger.event.data.currency }}{{ trigger.event.data.amount }}
```

Amounts use Up's signed decimal representation: an outgoing purchase is normally negative.

## Webhooks and polling

Up webhooks are signed using `X-Up-Authenticity-Signature` with an HMAC-SHA256 secret returned only when the webhook is created. They are useful for faster events, but the target must be a public URL that Up can reach and respond to with HTTP 200. That requires exposing Home Assistant through a securely configured public URL or using a separate relay; it also needs secure secret lifecycle handling. This initial release deliberately does not create webhooks or expose an endpoint. The default five-minute polling is private, requires no inbound access, and catches up after downtime.

## Limits and behaviour

- Up is a cloud API, so values cannot update while the API or Internet connection is unavailable.
- Polling is not instant. A transaction can be held, settled, or (for an abandoned hold) deleted; those changes generate distinct events when observed. A very large backlog beyond the API pagination safety limit may need a later refresh; normal outages are handled.
- Home loans are displayed if selected because the current Up API lists them; the original focus is personal, 2Up, and Saver accounts.
- This integration is read-only. It does not create transactions, modify categories, sync budgets, or mirror full financial history into Home Assistant.

## Updating

Use HACS's update button when a release is available, then restart Home Assistant. For a manual install, replace the integration directory and restart. Before updating, make a Home Assistant backup as usual.

## Development

The implementation uses Home Assistant's built-in HTTP client and coordinator—there is no third-party API client to maintain. Run the checks with a Home Assistant development environment:

```powershell
python -m compileall custom_components
python -m pytest
```

`tests/test_models.py` covers the account UI label and the compact automation event contract. Integration behaviour should additionally be exercised against Up's demo API token in an isolated Home Assistant development instance.
