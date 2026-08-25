pipeline {
    agent any

    environment {
        // 从 Jenkins Credentials 读取，不写入代码库
        BASE_URL          = credentials('BASE_URL')
        AUTHORIZATION     = credentials('AUTHORIZATION')
        CLIENT_ID         = credentials('CLIENT_ID')
        REFERENCE_IMAGE_URL = credentials('REFERENCE_IMAGE_URL')
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'master',
                    url: 'https://github.com/tagaki39/image_test.git',
                    credentialsId: 'github-credentials'
            }
        }

        stage('Build Test Image') {
            steps {
                // 构建测试镜像（首次较慢，之后走 Docker 层缓存）
                sh 'docker build -t image-api-test .'
            }
        }

        stage('Fast Tests (not costly)') {
            steps {
                // 用镜像跑非生成类用例，凭据通过环境变量注入，不落盘
                // docker run 的 -v 源路径会被宿主 daemon 解析，拿不到报告，
                // 因此用 docker cp 把容器内报告导出到 Jenkins workspace
                sh '''
                    # Jenkins sh 默认 -e，测试失败(exit 1)会中断脚本，先关掉
                    set +e
                    # 清理上次构建可能残留的同名容器
                    docker rm -f fast-tests 2>/dev/null || true
                    docker run --name fast-tests \
                        -e BASE_URL="${BASE_URL}" \
                        -e AUTHORIZATION="${AUTHORIZATION}" \
                        -e CLIENT_ID="${CLIENT_ID}" \
                        -e REFERENCE_IMAGE_URL="${REFERENCE_IMAGE_URL}" \
                        image-api-test
                    result=$?
                    set -e
                    # 无论测试成败都导出报告
                    docker cp fast-tests:/app/reports/. "$PWD/reports/" || true
                    docker rm -f fast-tests || true
                    exit $result
                '''
            }
            post {
                always {
                    publishHTML([
                        reportDir: 'reports',
                        reportFiles: 'report.html',
                        reportName: 'Fast Test Report',
                        keepAll: true,
                        alwaysLinkToLastBuild: true,
                        allowMissing: true,
                    ])
                }
            }
        }

        stage('Full Tests (costly)') {
            when {
                // 只在手动触发时跑全部用例（含真实AI生成，会产生费用）
                triggeredBy 'UserIdCause'
            }
            steps {
                sh '''
                    set +e
                    docker rm -f full-tests 2>/dev/null || true
                    docker run --name full-tests \
                        -e BASE_URL="${BASE_URL}" \
                        -e AUTHORIZATION="${AUTHORIZATION}" \
                        -e CLIENT_ID="${CLIENT_ID}" \
                        -e REFERENCE_IMAGE_URL="${REFERENCE_IMAGE_URL}" \
                        image-api-test pytest --html=reports/full-report.html --self-contained-html
                    result=$?
                    set -e
                    docker cp full-tests:/app/reports/. "$PWD/reports-full/" || true
                    docker rm -f full-tests || true
                    exit $result
                '''
            }
            post {
                always {
                    publishHTML([
                        reportDir: 'reports-full',
                        reportFiles: 'full-report.html',
                        reportName: 'Full Test Report',
                        keepAll: true,
                        alwaysLinkToLastBuild: true,
                        allowMissing: true,
                    ])
                }
            }
        }
    }

    post {
        success {
            emailext(
                subject: "✅ 测试通过 - ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                body: "本次构建通过。\n报告: ${env.BUILD_URL}",
                to: '3419830536@qq.com'
            )
        }
        failure {
            emailext(
                subject: "❌ 测试失败 - ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                body: "请检查报告: ${env.BUILD_URL}",
                to: '3419830536@qq.com'
            )
        }
    }
}
