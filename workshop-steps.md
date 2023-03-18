# Workshop Steps

## Infrastructure as Code (cloudformation)

1. Create a new repo using the workshop repo template: https://github.com/wizeline/vulnerabilities-scanner-template.
      ![new repo](img/2022-12-06-14-18-13.png)
2. This template contains:
   1. Sample cloudformation code
   2. Sample python code that is going to be deployed as lambdas
   3. Sample dockerized app
3. Clone the repo you just forked

    `git clone git@github.com:USERNAME/vulnerabilities-scanner-workshop.git`

4. Please note directory `/final_solution/` contains all demo files in its final stage, meaning you can easily copy and paste the respective files by following the instructions here and be able to proceed with pipeline without any failures, however we strongly suggest to follow along to see every step for each tool fail, and it's respective solution accordingly.
5. Create the IaC workflow on: `.github/workflows/ci-iac.yml`.
6. Identify programming errors, bugs, stylistic errors and suspicious constructs by adding Linter or **lint job**.
   1. Copy the following code to pipeline file created:

      ```yml
      name: CI Infra as Code

      on:
        [workflow_dispatch, push]

      concurrency: ci-${{ github.ref }}

      jobs:

        lint:
          name: CloudFormation Linter
          runs-on: ubuntu-latest
          steps:
            - name: Check out Git repository
              uses: actions/checkout@v3

            - name: Setup CloudFormation Linter with Latest Version
              uses: scottbrenner/cfn-lint-action@v2

            - name: Lint CloudFormation files.
              run: |
                cfn-lint --version
                cfn-lint -t cfn/*.y*ml -I

      ```

   2. Push your changes.
   3. Check output to identify possible errors.
   4. Let's fix the warning from the scan job by creating file at repository root level named `.cfnlintrc.yml` or using command-line `touch .cfnlintrc.yml` and add following content:

      ```yml
      ignore_checks:
        - W3002 # This code may only work with `package` cli command as the property (Resources/emailSender/Properties/Code) is a string
      ```

   5. Save and push your changes.
   <br/>
   <br/>
7. Implement Security Scanner: *Aqua Security Trivy*
   1. Add the following code to your pipeline file `ci-iac.yml`:
      ```yml
          trivy:
            name: Run Trivy (Iac and fs mode)
            runs-on: ubuntu-latest
            steps:
              - name: Check out Git repository
                uses: actions/checkout@v3

              # Trivy scans Infrastructure as Code (IaC) Terraform, CloudFormation, Dockerfile and Kubernetes.
              - name: Run Trivy vulnerability scanner in IaC mode
                uses: aquasecurity/trivy-action@master
                with:
                  scan-type: 'config'
                  hide-progress: false
                  format: 'table'
                  exit-code: '1'
                  ignore-unfixed: false
                  severity: 'UNKNOWN,LOW,MEDIUM,HIGH,CRITICAL'

              - name: Run Trivy vulnerability scanner in fs mode
                uses: aquasecurity/trivy-action@master
                with:
                  scan-type: 'fs'
                  hide-progress: false
                  format: 'table'
                  exit-code: '1'
                  ignore-unfixed: false
                  severity: 'UNKNOWN,LOW,MEDIUM,HIGH,CRITICAL'
      ```
   2. Save and push your changes.
   3. Check output for possible vulnerabilities.
   4. If pipeline failed for flag: *Image user should not be ‘root’* Reference Link: https://avd.aquasec.com/misconfig/ds002
   5. Fix the issue by creating a file named `.trivyignore` at root level of your repository and add the following content:

         Reference link: [trivy DS-0002](https://avd.aquasec.com/misconfig/dockerfile/general/avd-ds-0002/)

         ```yml
         # Running containers with 'root' user can lead to a container escape situation. It is a best practice to run containers as non-root users, which can be done by adding a 'USER' statement to the Dockerfile.
         DS002
         ```
   6. Save and push your changes.
   7. Check output pipeline status.
   8. Trivy possibly identified a vulnerability with CVE-2022-42969, you can find more details [HERE](https://avd.aquasec.com/nvd/2022/cve-2022-42969/). You can deep dive into the subject on your own:
   ![CVE-2022-42969](img/2022-11-17-8-37-59.png)
   For now, let's ignore this flag by changing a value under trivy scanner fs mode code, look for parameter ->> *ignore-unfixed* and set value = true:

        ```yml
              - name: Run Trivy vulnerability scanner in fs mode
                uses: aquasecurity/trivy-action@master
                with:
                  scan-type: 'fs'
                  hide-progress: false
                  format: 'table'
                  exit-code: '1'
                  ignore-unfixed: true
                  severity: 'UNKNOWN,LOW,MEDIUM,HIGH,CRITICAL'
        ```
   <br/>
   <br/>
8. In this step, let's look for patterns in our CloudFormation templates that may indicate insecure infrastructure, we will use ***stelligent/cfn_nag*** in our pipeline for this purpose.
   1. Add the following code to pipeline file created:
      ```yml
          insecure-cf:
            name: Scan Insecure Cloudformation patterns
            runs-on: ubuntu-latest
            steps:
              - name: Check out Git repository
                uses: actions/checkout@v3

              - name: Insecure Cloudformation patterns
                uses: stelligent/cfn_nag@master
                with:
                  input_path: cfn
                  extra_args: --fail-on-warnings

              - name: Fail if cfn_nag scan contains failures, warnings
                # sum cfn_nag failures, warnigns and return it as exit code
                run: |
                  exit `grep -E '^(Failures|Warnings)' cfn_nag.out | awk '{ SUM += $3} END { print SUM }'`
      ```
   2. Push your changes.
   3. Check scan resultset, notice the different warinings listed and create a plan of action on a real environment; For now, lets skip the warnings in order to continue.
   ![stelligent warning](img/2022-11-18-12-17-18.png)
   4.  Add an exception file for those warinings at repository root level named `.cfnnagcfg.yml` or using command-line `touch .cfnnagcfg.yml` and add the below rules to supress on scan:
        ```yml
        ---
        RulesToSuppress:
        - id: W2
          reason: Security Groups found with cidr open to world on ingress.  This should never be true on instance.  Permissible on ELB
        - id: W9
          reason: Security Groups found with ingress cidr that is not /32
        - id: W58
          reason: Lambda functions require permission to write CloudWatch Logs
        - id: W92
          reason: Lambda functions should define ReservedConcurrentExecutions to reserve simultaneous executions
        - id: F1000
          reason: Missing egress rule means all traffic is allowed outbound.  Make this explicit if it is desired configuration
        ```
   5. Lets add an additional extra argumement ` --deny-list-path .cfnnagcfg.yml` to the job to consider the exception file:
        ```yml
              - name: Insecure Cloudformation patterns
                uses: stelligent/cfn_nag@master
                with:
                  input_path: cfn
                  extra_args: --fail-on-warnings --deny-list-path .cfnnagcfg.yml
        ```

    6. Save and Push your changes.
    7. If no errors, let's continue...
<br/>
<br/>

1. *Checkov*: Policy-as-code. Scans cloud infrastructure configurations to find misconfigurations.
   1. Add the following code to pipeline file created:
      ```yml
          Checkov:
            name: Checkov - Security Analysis of Cloudformation
            runs-on: ubuntu-latest
            steps:
              - name: Check out Git repository
                uses: actions/checkout@v3

              - name: Run Checkov action
                id: checkov
                uses: bridgecrewio/checkov-action@master
                with:
                  directory: cfn/
                  quiet: false # optional: display only failed checks
                  soft_fail: false # optional: do not return an error code if there are failed checks
                  #skip_check: CKV_AWS_115,CKV_AWS_116,CKV_AWS_173,CKV_AWS_260
        ```
    2. Commit and Push your changes.
    3. Static security analysis show diffent validation flags from the scan.
    ![checkov scan](img/2022-11-18-1-38-26.png)
    4. For thew purpose of the demo, we will skip those flags by uncomment the parameter *skip_check* as below:
        ```yml
              - name: Run Checkov action
                  id: checkov
                  uses: bridgecrewio/checkov-action@master
                  with:
                  directory: cfn/
                  quiet: false # optional: display only failed checks
                  soft_fail: false # optional: do not return an error code if there are failed checks
                  skip_check: CKV_AWS_115,CKV_AWS_116,CKV_AWS_173,CKV_AWS_260
        ```
    5. Save and push your changes.
    6. If no errors, let's continue...
<br/>
<br/>

1. Add final job to validate all previous steps `[checkov,insecure-cf,trivy,lint]` are completed, if any of those fail it will not complete.
   1. Add the following code to pipeline file created:
      ```yml
          deploy:
            name: deploy
            needs: [checkov,insecure-cf,trivy,lint]
            runs-on: ubuntu-latest
            steps:
              - name: Deploy the thing
                run: |
                  echo Deploying 🚀
      ```
<br/>

## Application Code (Python)

Let's now create our CI pipeline for the application and explore the different tools that will help you to secure your deployments and pipelines.

1. Let's start by creating our pipeline file `.github/workflows/ci-app.yml`.
2. ***trufflehog***: is an open source secrets detection engine that finds leaky API keys and passwords
   1. Add the following code to pipeline file created:
      ```yml
        name: CI App
        on:
          [workflow_dispatch, push]

        concurrency: ci-app-${{ github.ref }}

        jobs:

          truffleHog:
            runs-on: ubuntu-latest
            steps:
              - name: Checkout code
                uses: actions/checkout@v3
                with:
                  fetch-depth: 0

              - name: trufflehog
                run: |
                  docker run -v ${PWD}:/truffle trufflesecurity/trufflehog:latest filesystem --directory="/truffle/"
      ```
3. ***Gitleaks***: This tool helps in detecting and preventing hardcoded secrets like passwords, api keys, and tokens in git.
   1. Add the following code to pipeline file created:
      ```yml
        gitleaks:
          name: gitleaks
          runs-on: ubuntu-latest
          steps:
            - uses: actions/checkout@v3
              with:
                fetch-depth: 0

            - name: run gitleaks docker
              run: |
                docker run -v ${PWD}:/path zricethezav/gitleaks:latest detect --source="/path/" -v -l debug --no-git
      ```
   2. Gitleaks performs leaks based on regex expressions, you can get more detail by checking file: `.gitleaks.toml`.
   3. Check output to identify possible leaks. As a best practice, never leave secrets exposed, even when those are commented lines, at the end is plain text that can be exploited.
   ![gitleaks results](img/2022-11-18-2-41-39.png)
   4. Check on gitleaks results for parameters found: *Finding*,*Secret*,*File*,*Line*.
   5. Fix flagged code on `lambda.py`, remove commented line that shows #token, and replace secrets value withe string: "test" as per code below (do not copy pointing arrows):
      ```yml
        def get_logs_client():
            """Get AWS logs client either local or real"""

            if IS_DEPLOYMENT:
                return boto3.client("logs", region_name=region_name)
            else:
                return boto3.client(
                    "logs",
                    aws_access_key_id="test", <-----
                    aws_secret_access_key="test", <-----
                    region_name=region_name,
                    endpoint_url="http://localhost:4566",
                )
      ```
    6. Save and push your changes.
   <br/>
   <br/>
4. ***PyCharm Security***: This tool allows you to run a security check to your repository.
   1. Add the bellow code to the `ci-app.yml` file:
      ```yml
        pycharm:
          runs-on: ubuntu-latest
          needs: [gitleaks,truffleHog]
          name: Pycharm-security check
          steps:
            - name: checkout git repository
              uses: actions/checkout@v3

            - name: Run PyCharm Security
              uses: tonybaloney/pycharm-security@master
      ```
    2. Save and Push your changes.
    3. Check on outputs for Pycharm-security check.
      ![Pycharm results](img/2022-11-16-2-48-13.png)
    4. Please notice that your pipeline continues even when warnings are flagged, if you want to modify this behaviour and force the pipeline to fail, this can be achieved by adding extra argument: `fail_on_warnings` and set that to `true`.
    5. You can explore this on your own; For the purpose of the demo, let's continue...
<br/>
<br/>

1. ***Grype (Anchore)***: Vulnerability scanner for container images and filesystems.
   1. Add the bellow code to the `ci-app.yml` file:
      ```yml
        docker-grype-project:
          name: Grype (Anchore) Project Scan
          needs: [gitleaks,truffleHog]
          runs-on: ubuntu-latest
          steps:
            - name: Check out Git repository
              uses: actions/checkout@v3

            - name: Scan current project with Grype (Anchore)
              id: scan-project
              uses: anchore/scan-action@v3
              with:
                path: "."
                fail-build: true
                output-format: table
      ```
   2. Save and push your changes.
   3. Check pipeline output; You should see the below vulnerability found, since we did specify parameter ***fail-build: true*** the job got failed, but you can change this behaviour by setting the value to ***false***.
   ![grype result](img/2022-11-18-4-46-19.png)
   4. Awesome!! Let's continue...
   <br/>
   <br/>
2. Now, lets create your Docker image.
   1. Add docker build job code block to `ci-app.yml` file:
      ```yml
          docker-build:
            name: Build Docker image
            outputs:
              full_docker_image_tag: ${{ steps.build_image.outputs.full_docker_image_tag }}
              image_tag: ${{ steps.build_image.outputs.image_tag }}
            runs-on: ubuntu-latest
            needs: [pycharm, docker-grype-project]
            steps:
              - name: Check out Git repository
                uses: actions/checkout@v3

              - name: Add SHORT_SHA and BRANCH_TAG env variables
                run: |
                  echo "SHORT_SHA=`echo ${GITHUB_SHA} | cut -c1-8`" >> $GITHUB_ENV
                  echo "BRANCH_TAG=`echo ${GITHUB_REF##*/}`" >> $GITHUB_ENV

              - name: Set IMAGE_TAG env variable
                run: |
                  echo "IMAGE_TAG=`echo ${BRANCH_TAG}-${SHORT_SHA}`" >> $GITHUB_ENV

              - name: Build and tag image
                id: build_image
                env:
                  REGISTRY: ghcr.io
                  IMAGE_NAME: ${{ github.repository }}
                  ECR_REPOSITORY: ${{ github.repository }}
                  IMAGE_TAG: ${{ env.IMAGE_TAG }}
                run: |
                  echo REGISTRY: $REGISTRY
                  echo ECR_REPOSITORY: $ECR_REPOSITORY
                  echo IMAGE_TAG: $IMAGE_TAG
                  echo "Building and tagging $REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG ..."
                  docker build -t $REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG -f Dockerfile .
                  mkdir -p /tmp
                  docker save "$REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG" > /tmp/docker-image.tar
                  echo "full_docker_image_tag=$REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG" >> $GITHUB_OUTPUT
                  echo "image_tag=$IMAGE_TAG" >> $GITHUB_OUTPUT

              - name: Upload artifact
                uses: actions/upload-artifact@v2
                with:
                  name: docker-image
                  path: /tmp/docker-image.tar
                  retention-days: 1
      ```

3. Lets scan our Docker image for vulnerabilities, add *Docker-trivy-vuln* job to pipeline.
   1. Add docker trivy job to `ci-app.yml` file:
      ```yml
          docker-trivy-vuln:
            name: Trivy vulnerability scanner
            runs-on: ubuntu-latest
            needs: [docker-build]
            steps:
              - name: Download artifact
                uses: actions/download-artifact@v3
                with:
                  name: docker-image
                  path: /tmp
              - name: Load Docker image
                run: |
                  docker load --input /tmp/docker-image.tar

              - name: Run Trivy vulnerability scanner
                uses: aquasecurity/trivy-action@master
                with:
                  image-ref: "${{ needs.docker-build.outputs.full_docker_image_tag }}"
                  hide-progress: false
                  format: 'table'
                  exit-code: '0'
                  ignore-unfixed: false
                  severity: 'UNKNOWN,LOW,MEDIUM,HIGH,CRITICAL'
      ```
    2. Push your changes.
    3. If no issues, let's continue...
<br/>
<br/>

1. Lets invoke our vulnerability scanner for container images - *Grype*:
    1.  Add below code to our `ci-app.yml` file:
        ```yml
            docker-grype:
              name: Grype (Anchore) Docker Scan
              runs-on: ubuntu-latest
              needs: [docker-build]
              steps:
                - name: Download artifact
                  uses: actions/download-artifact@v2
                  with:
                    name: docker-image
                    path: /tmp

                - name: Load Docker image
                  run: |
                    docker load --input /tmp/docker-image.tar

                - name: Scan image wih Grype (Anchore)
                  id: scan-image
                  uses: anchore/scan-action@v3
                  with:
                    image: "${{ needs.docker-build.outputs.full_docker_image_tag }}"
                    output-format: table
                    fail-build: true
        ```
    2. Push your changes
    3. Check pipeline output; You should see the below vulnerability found, since we did specify parameter `fail-build: true` the job got failed, but you can change this behaviour by setting the value to `false`.
    4. If no issues, let's continue..
<br/>
<br/>

1. Our final step is a validation job which depends on previous security scans in order to complete:
    1. Add the below job and push your changes:
      ```yml
          deploy:
            name: deploy
            runs-on: ubuntu-latest
            needs: [docker-grype,docker-trivy-vuln]
            steps:
              - name: Deploy the thing
                run: |
                  echo Deploying 🚀
      ```
2. If pipeline succeeded, you are all set!!!!!!
3. Happy deploy... 🚀
