# multiplayer-ping-pong

## Install dependencies

Ensure that both the server and client computers have the required packages

```python
pip install -r requirements.txt
```

## Server

Run the server script

```python
python src/server.py
```

## User Clients

Use the host IPv4 address and port specified by the server to start the client

```python
python src/client.py <host> <port> <TEAM>
```

where `<TEAM>` is `LEFT` or `RIGHT`.

## AI Clients

Use the host IPv4 address and port specified by the server to start the AI client

```python
python src/ai_client.py <host> <port> <TEAM>
```

where `<TEAM>` is `LEFT` or `RIGHT`.
