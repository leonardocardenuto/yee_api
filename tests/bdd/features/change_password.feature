Feature: Change password functionality

Scenario: Password changed successfully
    Given I am a registered user and forgot my password
    When I create a new password and confirm it
    Then the password should be changed in the database

Scenario: New password and new password confirmation doesnt match
    Given I am a registered user and forgot my password
    When I enter a new password and its confirmation and they do not match
    Then I should see an error message and the password is not changed in the database