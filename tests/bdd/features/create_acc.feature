Feature: Create account functionality

Scenario: Successful registration
    Given I have a valid email
    When I fill the form
    Then I should be registered successfully

Scenario: Invalid email
    Given I do not have a valid email
    When I fill the form with the invalid email and the rest of info
    Then I should see an error message stating that for some reason it did not work
