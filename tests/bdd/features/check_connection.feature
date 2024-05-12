Feature: Connection Neon DB functionality

Scenario: Successful Connection
    Given a valid database uri
    When attempts to connect
    Then it should connect successfully
