const tournamentStub = {
  name: "Tournament name",
  acronym: "ACRONYM",
};

describe("Tournament page initial load", () => {
  it("Visits the tournament page", () => {
    cy.intercept(
      {
        method: "GET",
        url: "http://localhost:5001/api/v1/tosurnament/tournaments/*",
      },
      tournamentStub // and force the response to be: []
    ).as("getTournament"); // and assign an alias
    cy.visit("/tournaments/1");
    cy.wait("@getTournament");
    cy.get(".tournament_name").should("have.value", tournamentStub.name);
    cy.get(".tournament_acronym").should("have.value", tournamentStub.acronym);
  });
});
