import org.gradle.api.tasks.testing.logging.TestLogEvent

allprojects {
    repositories {
        mavenCentral()
    }
}

subprojects {
    apply(plugin = "java")

    java {
        toolchain {
            languageVersion.set(JavaLanguageVersion.of(21))
        }
    }

    tasks.withType<org.gradle.api.tasks.compile.JavaCompile> {
        options.encoding = "UTF-8"
    }

    dependencies {
        testImplementation(platform("org.junit:junit-bom:5.10.2"))
        testImplementation("org.junit.jupiter:junit-jupiter")
    }

    tasks.withType<Test> {
        useJUnitPlatform()
        testLogging {
            events = setOf(TestLogEvent.FAILED)
            showExceptions = true
            exceptionFormat = org.gradle.api.tasks.testing.logging.TestExceptionFormat.FULL
        }
    }
}
