Feature: Login functionality

Scenario: Successful login
    Given I am a registered user
    When I enter my correct username and password
    Then I should be logged in successfully

Scenario: Incorrect username or password
    Given I am a registered user
    When I enter an incorrect username or password
    Then I should see an error message
