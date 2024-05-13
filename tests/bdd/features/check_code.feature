Feature: Verify the verification code sent by the user is correct

Scenario: Code in the db is the same that the user submitted
    Given I am a registered user and forgot my password
    When I submmit the verification code sent in my email
    Then I should be verified

Scenario: Code in the db is not the same that the user submitted
    Given I am a registered user and forgot my password
    When I submmit the wrong verification code
    Then I should see an error message