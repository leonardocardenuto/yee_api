Feature: Generate Code functionality

Scenario: Successful Generation
    Given a valid email to  generate the code
    When attempts to generate
    Then it should generate successfully

Scenario: Failed Generation
    Given a invalid email to  generate the code
    When attempts to generate it with a wrong email
    Then it should show some kind of error