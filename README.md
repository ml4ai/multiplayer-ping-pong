# multiplayer-ping-pong

## Install dependencies

Require Python >= 3.6. Ensure that both the server and client computers have the required packages

```python
pip3 install -r requirements.txt
```

## Server

Run the server script.

```python
python3 src/server.py <host>
```

where `<host>` is IPv4 address of host computer.

Available server commands:

- `h` or `help`: List of server commands
- `pause`: Pause the game
- `unpause`: Unpause the game
- `restart`: Reset and pause the game
- `exit`: Close the game on server and clients

DANGER: Do not interrupt the game from the terminal.

## User Clients

Use the host IPv4 address and port specified by the server to start the client.

```python
python3 src/client.py <host> <port> <TEAM>
```

where `<TEAM>` is `LEFT` or `RIGHT`.

To exit the game, close the game screen or type `exit` into the terminal.

DANGER: Do not interrupt the game from the terminal.

## AI Clients

Use the host IPv4 address and port specified by the server to start the AI client.

```python
python3 src/ai_client.py <host> <port> <TEAM>
```

where `<TEAM>` is `LEFT` or `RIGHT`.

To exit the AI client, type `exit` on the terminal that runs the AI client.

DANGER: Do not interrupt the game from the terminal.
