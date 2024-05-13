Feature: Reset Pass functionality

Scenario: Successful Reset
    Given I forgot my password
    When I insert a new one and confirm it
    Then it should be changed

Scenario: Failed Reset
    Given I forgot my password and I make a mistake
    When I insert a new one and confirm it and they dont match
    Then it should display an error
