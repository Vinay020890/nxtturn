describe('User Profile - Resume Tab', () => {
  const testUser = {
    username: 'resumeTester',
    email: 'resume_test@example.com',
    password: 'password123',
    first_name: 'Resume',
    last_name: 'Expert',
  }

  before(() => {
    cy.testSetup('create_user', testUser)
  })

  beforeEach(() => {
    cy.intercept('GET', `/api/profiles/${testUser.username}/`).as('getProfile')
    cy.login(testUser.email, testUser.password)
    cy.visit(`/profile/${testUser.username}`)
    cy.wait('@getProfile')

    // Navigate to Resume Tab - ensure button is visible before clicking
    cy.contains('button', 'Resume').should('be.visible').click()
  })

  it('allows a user to upload, view, and delete a resume PDF', () => {
    // 1. Initial State - Check for Header and Button instead of specific paragraph text
    cy.contains('h3', 'Resume / CV').should('be.visible')
    cy.get('[data-cy="upload-resume-button"]').should('be.visible').and('contain', 'Upload PDF')

    // 2. Upload Action
    cy.intercept('PATCH', `/api/profiles/${testUser.username}/`).as('uploadResume')

    // Select the file (Creating a dummy PDF buffer)
    cy.get('input[type="file"]').selectFile(
      {
        contents: Cypress.Buffer.from('%PDF-1.4 dummy content'),
        fileName: 'my_resume.pdf',
        mimeType: 'application/pdf',
      },
      { force: true },
    )

    cy.wait('@uploadResume').its('response.statusCode').should('eq', 200)
    cy.contains('Resume uploaded successfully!').should('be.visible')

    // 3. Verify Success State (View Mode)
    cy.get('[data-cy="view-resume-link"]').should('have.attr', 'target', '_blank')
    cy.get('[data-cy="delete-resume-button"]').should('be.visible')
    cy.contains('Curriculum Vitae').should('be.visible')

    // 4. Delete Action
    cy.intercept('PATCH', `/api/profiles/${testUser.username}/`).as('removeResume')
    cy.get('[data-cy="delete-resume-button"]').click()

    // Confirm the browser alert automatically
    cy.on('window:confirm', () => true)

    cy.wait('@removeResume').its('response.statusCode').should('eq', 200)
    cy.contains('Resume removed').should('be.visible')

    // 5. Verify return to empty state (Upload Mode)
    cy.get('[data-cy="upload-resume-button"]').should('be.visible').and('contain', 'Upload PDF')
    cy.contains('Curriculum Vitae').should('not.exist')
  })
})
