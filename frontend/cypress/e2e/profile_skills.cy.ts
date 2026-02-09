describe('User Profile - Skills Tab', () => {
  const testUser = {
    username: 'skillTester',
    email: 'skill_test@example.com',
    password: 'password123',
    first_name: 'Skill',
    last_name: 'Master',
  }

  before(() => {
    cy.testSetup('create_user', testUser)
  })

  beforeEach(() => {
    // 1. Setup Intercepts
    cy.intercept('GET', `/api/profiles/${testUser.username}/`).as('getProfile')
    cy.intercept('POST', '/api/profile/skill-categories/').as('createCategory')
    cy.intercept('POST', '/api/profile/skills/').as('addSkill')
    cy.intercept('DELETE', '/api/profile/skill-categories/*/').as('deleteCategory')

    // 2. Login & Visit
    cy.login(testUser.email, testUser.password)
    cy.visit(`/profile/${testUser.username}`)
    cy.wait('@getProfile')

    // 3. SWITCH TO SKILLS TAB (This was missing)
    cy.contains('button', 'Skills').click()

    // 4. Verify we are on the Skills tab (Wait for empty state or content)
    // The test expects "No skills added yet." initially for a new user.
    cy.contains('No skills added yet.').should('be.visible')
  })

  it('allows full lifecycle: Create Category -> Add Skills -> Delete Category', () => {
    const categoryName = 'Frontend Magic'
    const skillName = 'Vue.js'

    // 1. Create Category
    cy.contains('button', 'Add Category').click()
    cy.contains('h3', 'Create New Category').should('be.visible')

    cy.get('input[placeholder^="e.g."]').type(categoryName)
    cy.intercept('POST', '/api/profile/skill-categories/').as('createCategory')
    cy.contains('button', 'Create').click()

    cy.wait('@createCategory').its('response.statusCode').should('eq', 201)
    cy.contains(categoryName).should('be.visible')

    // 2. Add Skill to Category
    // Click the Edit (Pencil) button on the category card
    cy.contains(categoryName).parent().find('button[title="Edit Category"]').click()

    cy.contains('h3', `Manage ${categoryName}`).should('be.visible')
    cy.contains('No skills in this category yet.').should('be.visible')

    // Type Skill and Add
    cy.get('input[placeholder^="Skill Name"]').type(skillName)
    cy.get('select').select('Expert') // Select proficiency

    cy.intercept('POST', '/api/profile/skills/').as('addSkill')
    // We use the new "Smart Done" feature: clicking Done saves the typed skill
    cy.contains('button', 'Done').click()

    cy.wait('@addSkill').its('response.statusCode').should('eq', 201)

    // 3. Verify Skill appears in the card
    cy.contains(categoryName)
      .parent()
      .parent()
      .within(() => {
        cy.contains(skillName).should('be.visible')
        cy.contains('Expert').should('be.visible')
      })

    // 4. Delete Category
    cy.intercept('DELETE', '/api/profile/skill-categories/*/').as('deleteCategory')
    cy.contains(categoryName).parent().find('button[title="Delete Category"]').click()

    cy.on('window:confirm', () => true)
    cy.wait('@deleteCategory').its('response.statusCode').should('eq', 204)

    // Verify Gone
    cy.contains(categoryName).should('not.exist')
    cy.contains('No skills added yet.').should('be.visible')
  })
})
