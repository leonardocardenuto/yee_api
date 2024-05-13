Feature: Generate verification code and send it by email

Scenario: Code Generated and sent by email successfully
    Given I am a registered user and forgot my password
    When I give my email
    Then the a random code should be changed generated, inserted in db and sent by email

Scenario: email not sent or code not generated / inserted in db
    Given I am a registered user and forgot my password
    When I give my email and it is not sent or the code is note inserted in db
    Then I should see an error message