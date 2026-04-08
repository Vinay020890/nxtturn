// C:\Users\Vinay\Project\frontend\cypress\e2e\profile_skills.cy.ts

describe('User Profile - Skills Tab', () => {
  const uniqueId = Date.now()
  const testUser = {
    username: `skillTester_${uniqueId}`,
    // Domain-locked to ensure manual accounts are never deleted
    email: `skill_${uniqueId}@cypresstest.com`,
    password: 'password123',
    first_name: 'Skill',
    last_name: 'Master',
  }

  before(() => {
    // SELF-HEALING: Clears data from any previous interrupted/crashed runs
    cy.testSetup('cleanup')
    cy.testSetup('create_user', testUser)
  })

  after(() => {
    // SELF-CLEANING: Wipes test data after a successful run
    cy.testSetup('cleanup')
  })

  beforeEach(() => {
    cy.intercept('GET', `/api/profiles/${testUser.username}/`).as('getProfile')
    cy.intercept('POST', '/api/profile/skill-categories/').as('createCategory')
    cy.intercept('POST', '/api/profile/skills/').as('addSkill')
    cy.intercept('DELETE', '/api/profile/skill-categories/*/').as('deleteCategory')

    cy.login(testUser.email, testUser.password)
    cy.visit(`/profile/${testUser.username}`)
    cy.wait('@getProfile')

    cy.contains('button', 'Skills').click()
    cy.contains('No skills added yet.').should('be.visible')
  })

  it('allows full lifecycle: Create Category -> Add Skills -> Delete Category', () => {
    const categoryName = `Frontend Magic ${uniqueId}`
    const skillName = 'Vue.js'

    // 1. Create Category
    cy.contains('button', 'Add Category').click()
    cy.get('input[placeholder^="e.g."]').type(categoryName)
    cy.contains('button', 'Create').click()
    cy.wait('@createCategory').its('response.statusCode').should('eq', 201)

    // 2. Add Skill to Category
    cy.contains(categoryName).parent().find('button[title="Edit Category"]').click()
    cy.get('input[placeholder^="Skill Name"]').type(skillName)
    cy.get('select').select('Expert')
    cy.contains('button', 'Done').click()
    cy.wait('@addSkill').its('response.statusCode').should('eq', 201)

    // 3. Verify
    cy.contains(categoryName)
      .parent()
      .parent()
      .within(() => {
        cy.contains(skillName).should('be.visible')
      })

    // 4. Delete
    cy.contains(categoryName).parent().find('button[title="Delete Category"]').click()
    cy.on('window:confirm', () => true)
    cy.wait('@deleteCategory').its('response.statusCode').should('eq', 204)
    cy.contains(categoryName).should('not.exist')
  })
})
