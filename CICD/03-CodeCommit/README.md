# AWS CodeCommit - Version Control

## What is AWS CodeCommit?

AWS CodeCommit is a secure, fully-managed source control service. It allows teams to collaborate on code development with:
- Git-based repositories
- Private repositories by default
- Branch management
- Pull requests with code review
- Webhook triggers for CI/CD
- Authentication with SSH/HTTPS
- Integration with CodePipeline

## CodeCommit vs GitHub/GitLab

| Feature | CodeCommit | GitHub | GitLab |
|---------|-----------|--------|--------|
| **Cost** | Free (5 users) | $0-231/month | Free-$228/month |
| **AWS Integration** | Native | Via API | Via API |
| **Private Repos** | Yes | Yes | Yes |
| **Code Review** | Basic | Advanced | Advanced |
| **CI/CD Integration** | CodePipeline | Actions | Pipelines |
| **Best For** | AWS-first orgs | General use | DevOps teams |

## Core Concepts

### Repository
- Container for project code
- Git-based
- Private by default
- Multiple branches
- Full commit history

### Branch
- Isolated version of code
- Main branch (default)
- Feature branches
- Release branches

### Commit
- Snapshot of changes
- Unique commit ID (SHA)
- Author, message, timestamp
- Parent commit reference

### Pull Request
- Request to merge code
- Code review mechanism
- Requires approval
- Automated checks

### Webhook
- Event trigger
- Notifies external services
- Triggers CodePipeline
- Real-time automation

## Creating a Repository

### Using AWS Console

#### Step 1: Navigate to CodeCommit
1. Go to AWS Console
2. Search for CodeCommit
3. Click "Create repository"

#### Step 2: Repository Settings
```
Repository Name: my-app
Description: My application repository
Default branch: main
Tags: Environment: dev, Team: backend
```

#### Step 3: Create
- Click "Create repository"
- Note the HTTPS and SSH URLs

### Using AWS CLI

```bash
# Create repository
aws codecommit create-repository \
    --repository-name my-app \
    --repository-description "My application" \
    --default-branch main

# Response includes:
# - cloneUrlHttp
# - cloneUrlSsh
# - repositoryArn
```

### Using Infrastructure as Code (CloudFormation)

```yaml
Resources:
  MyRepository:
    Type: AWS::CodeCommit::Repository
    Properties:
      RepositoryName: my-app
      Description: My application repository
      DefaultBranch: main
      Tags:
        - Key: Environment
          Value: dev
```

## Clone Repository

### HTTPS (Easier for Windows)
```bash
git clone https://git-codecommit.[region].amazonaws.com/v1/repos/my-app
cd my-app
```

### SSH (More secure)
```bash
git clone ssh://git-codecommit.[region].amazonaws.com/v1/repos/my-app
cd my-app
```

## User Access Control

### IAM User Permissions

#### Minimal CodeCommit Access
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "codecommit:Create*",
        "codecommit:Get*",
        "codecommit:List*",
        "codecommit:Describe*",
        "codecommit:PutCommentReaction",
        "codecommit:PostCommentForPullRequest",
        "codecommit:PostCommentForComparedCommit"
      ],
      "Resource": "*"
    }
  ]
}
```

#### Full Push/Pull Access
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "codecommit:*"
      ],
      "Resource": "arn:aws:codecommit:*:*:my-app"
    }
  ]
}
```

#### Repository-Specific Access
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "codecommit:GitPull",
        "codecommit:GitPush"
      ],
      "Resource": "arn:aws:codecommit:*:*:my-app"
    },
    {
      "Effect": "Deny",
      "Action": [
        "codecommit:DeleteBranch",
        "codecommit:PutRepositoryTriggers"
      ],
      "Resource": "arn:aws:codecommit:*:*:my-app"
    }
  ]
}
```

## Branch Management

### Create Branch

```bash
# Checkout main
git checkout main

# Pull latest changes
git pull origin main

# Create new branch from main
git checkout -b feature/add-login

# Push branch to CodeCommit
git push -u origin feature/add-login
```

### Branch Naming Convention

```
feature/add-user-authentication      # New features
hotfix/fix-login-bug                # Production bug fixes
release/v1.2.0                      # Release preparation
chore/update-dependencies           # Maintenance tasks
docs/api-documentation              # Documentation updates
```

### Protect Main Branch

#### Using AWS Console
1. Go to Repository Settings
2. Click "Approval rules"
3. Create rule:
   - Require approval count: 1
   - Exception: None
   - Resource for approver: Team members

#### Using CLI
```bash
aws codecommit create-approval-rule-template \
    --approval-rule-template-name protect-main \
    --approval-rule-template-content '{"Version": "2018-11-08","Statement": [{"Type": "Approvers","NumberOfApprovalsNeeded": 1,"ApprovalPoolMembers": ["arn:aws:iam::[account]:user/*"]}]}'

aws codecommit associate-approval-rule-template-with-repository \
    --repository-name my-app \
    --approval-rule-template-name protect-main
```

## Commit Workflow

### Create Local Commits

```bash
# Make code changes
# Edit files...

# Check status
git status

# Stage changes
git add .
# or specific files
git add src/main.js

# Commit with message
git commit -m "Add login feature"

# View commit
git log --oneline
```

### Commit Message Guidelines

```
Format: [Type] Subject

Types:
  feat:     New feature
  fix:      Bug fix
  docs:     Documentation
  style:    Formatting
  refactor: Code reorganization
  test:     Test addition
  chore:    Maintenance

Examples:
  feat: Add user authentication
  fix: Resolve memory leak in API
  docs: Update README
  chore: Update dependencies
```

### Push Commits to CodeCommit

```bash
# Push current branch
git push origin feature/add-login

# Push all branches
git push --all

# Push with tags
git push --tags

# Force push (use carefully!)
git push --force-with-lease
```

## Pull Requests (Code Review)

### Create Pull Request

#### Using AWS Console
1. Go to CodeCommit repository
2. Click "Pull requests"
3. Click "Create pull request"
4. Select source and destination branches
5. Add title and description
6. Add reviewers
7. Click "Create"

#### Using CLI
```bash
aws codecommit create-pull-request \
    --title "Add login feature" \
    --description "Adds user authentication with email/password" \
    --targets "[{\"repositoryName\":\"my-app\",\"sourceReference\":\"feature/add-login\",\"destinationReference\":\"main\"}]"
```

### Pull Request Template

Create `.github/PULL_REQUEST_TEMPLATE.md`:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] New feature
- [ ] Bug fix
- [ ] Breaking change
- [ ] Documentation update

## Testing Done
- [ ] Unit tests
- [ ] Integration tests
- [ ] Manual testing

## Screenshots (if applicable)
<!-- Add screenshots for UI changes -->

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] No new warnings generated
- [ ] Tests pass locally
```

### Review Process

```bash
# Reviewer: Get branch
git fetch origin feature/add-login

# Reviewer: Review commits
git log origin/main..origin/feature/add-login

# Reviewer: Review changes
git diff origin/main..origin/feature/add-login

# After review, approve in console
```

### Merge Pull Request

#### Using Console
1. Go to pull request
2. Click "Review"
3. Approve and merge
4. Delete branch after merge

#### Using CLI
```bash
aws codecommit merge-pull-request-by-fast-forward \
    --pull-request-id 1 \
    --repository-name my-app
```

## Triggers and Webhooks

### Create Repository Trigger

```bash
aws codecommit put-repository-triggers \
    --repository-name my-app \
    --triggers '[
      {
        "Name": "trigger-codepipeline",
        "DestinationArn": "arn:aws:codepipeline:us-east-1:123456789:my-pipeline",
        "Branches": ["main", "develop"],
        "Events": ["all"]
      }
    ]'
```

### Trigger Events

| Event | Trigger Condition |
|-------|------------------|
| **all** | Any event |
| **pushToReferenceTypeHead** | Push to branch |
| **pushToReferenceTypeTag** | Push of tag |
| **pullRequestCreated** | PR created |
| **pullRequestMerged** | PR merged |

## Code Review Rules

### Approval Rules

```bash
# Create approval rule
aws codecommit create-approval-rule-template \
    --approval-rule-template-name standard-review \
    --approval-rule-template-content '{
      "Version": "2018-11-08",
      "Statement": [
        {
          "Type": "Approvers",
          "NumberOfApprovalsNeeded": 2,
          "ApprovalPoolMembers": ["arn:aws:iam::123456789:user/developer1"]
        }
      ]
    }'
```

## Working with Remote Branches

```bash
# List all branches
git branch -a

# List remote branches only
git branch -r

# Fetch latest from remote
git fetch origin

# Delete local branch
git branch -d feature/old-feature

# Delete remote branch
git push origin --delete feature/old-feature

# Rename branch
git branch -m feature/old-name feature/new-name
git push origin :feature/old-name feature/new-name
```

## Handling Conflicts

```bash
# Update main
git checkout main
git pull origin main

# Rebase feature branch
git checkout feature/add-login
git rebase main

# If conflicts occur, resolve them:
# 1. Edit conflicting files
# 2. Remove conflict markers
# 3. Stage resolved files
git add resolved-file.js

# Continue rebase
git rebase --continue

# Push updated branch
git push -f origin feature/add-login
```

## IAM Policies for CI/CD Services

### CodePipeline Service Role

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "codecommit:GetBranch",
        "codecommit:GetCommit",
        "codecommit:UploadArchive",
        "codecommit:GetUploadArchiveStatus"
      ],
      "Resource": "arn:aws:codecommit:*:*:my-app"
    }
  ]
}
```

### CodeBuild Service Role

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "codecommit:GitPull"
      ],
      "Resource": "arn:aws:codecommit:*:*:my-app"
    }
  ]
}
```

## Common Commands Reference

```bash
# View repository info
aws codecommit get-repository --repository-name my-app

# Get default branch
aws codecommit get-repository \
    --repository-name my-app \
    --query 'repositoryMetadata.defaultBranch'

# List commits
aws codecommit get-commit-history --repository-name my-app --max-results 10

# Get file content
aws codecommit get-file \
    --repository-name my-app \
    --commit-specifier main \
    --file-path src/main.js
```

## Troubleshooting

### Authentication Errors
```bash
# Clear credentials
git credential-manager uninstall
git credential-manager install

# Or remove cached credentials
git config --global --unset credential.helper
```

### Branch Issues
```bash
# Recover deleted branch (within 30 days)
git reflog
git checkout -b recovered-branch commit-hash

# View all refs
git show-ref
```

### Push Failures
```bash
# Pull before push
git pull origin main

# Rebase if needed
git rebase origin/main

# Push again
git push origin feature/branch-name
```

## Best Practices

✅ Pull latest before starting work
✅ Use descriptive branch names
✅ Create pull requests for code review
✅ Require approvals before merge
✅ Protect main branch
✅ Delete merged branches
✅ Use conventional commit messages
✅ Keep commits small and focused
✅ Link to issues/tickets in PR description

## Next Steps

1. Create CodeCommit repository
2. Clone locally
3. Setup branch protection
4. Configure triggers for CodePipeline
5. Invite team members
6. Read [CodeBuild Guide](../04-CodeBuild/README.md)

## Summary

- **CodeCommit** = Git repository service
- **Branches** = Isolated code versions
- **Pull Requests** = Code review mechanism
- **Triggers** = Automated pipeline execution
- **IAM Policies** = Access control
- **Webhooks** = Real-time notifications
- **Protection Rules** = Main branch safety

---

**Next**: [CodeBuild Guide](../04-CodeBuild/README.md)
