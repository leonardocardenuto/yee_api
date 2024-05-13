Feature: Check Code functionality

Scenario: Successful Checking
    Given a valid code
    When attempts to check the code
    Then it should be successfull

Scenario: Failed Checking
    Given a invalid code
    When attempts to check the wrong code
    Then it should fail on checking
