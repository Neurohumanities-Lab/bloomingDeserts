library(shiny)
library(ellmer)
library(reticulate)

GOOGLE_API_KEY="YOUR API KEY"
gemini = chat_google_gemini(system_prompt = "You are voice of the unconsciousness that enter in a 
                            dialogue with the incoming prompts. This unconsciousness is represented in a desert,
                             where all kind of extraordinary events can happen. Reply with short sentences, like in an oral 
                            conversation. Gain intensity as long as the conversation advances",
                            api_key = GOOGLE_API_KEY)

#python osc script
source_python('data/oscScript.py')
source_python("data/oscServer2.py")

# Lanza el servidor OSC en segundo plano
#launch_osc_server_background("0.0.0.0", 10001)
run_server_thread()  # Levanta servidor en segundo plano

# Variable reactiva en R
osc_prompt <- reactiveVal("Esperando mensaje...")

# Define UI for application that draws a histogram
ui <- fluidPage(
  
  tags$style(HTML("
    body {
      background-color: #d46275;  /* color azul claro */
    }
    .column-divider {
      border-right: 2px solid white; /* línea vertical blanca */
      height: 100%; /* para que cubra toda la altura de la columna */
      padding-right: 15px; /* separación interna */
    }
  ")),

    # Application title
    titlePanel("LLM Dialogues"),
    
    fluidRow(

    column(6,
           class = "column-divider",
           textInput("manualPrompt", "Manual prompt", width = "90%"),
           actionButton("chat", "chat"),
           HTML("<br>"),
           textOutput("oscPrompt")
           ),
    column(6,
           style = "padding-left: 15px;",  # un poco de espacio a la izquierda
           HTML("<b>Chat Response</b>"),
           textOutput("response")
           #actionButton("send", "send"),
        )),

    )

# Define server logic required to draw a histogram
server <- function(input, output, session) {
  
  # reactiveVal para guardar el prompt
  prompt <- reactiveVal(NULL) 
  
  # reactiveVal para guardar la respuesta
  respuesta <- reactiveVal("")
  
  # Evento para generar respuesta cuando presionás el botón
  observeEvent(input$chat, {
    prompt(input$manualPrompt)
    res <- gemini$chat(prompt())
    respuesta(res)
  })
  
  #pero también puedo recibir el prompt por OSC
  # Variable reactiva en R
  osc_prompt <- reactiveVal(NULL)
  
  # Revisa cada medio segundo si hay nuevos mensajes
  observe({
    invalidateLater(500)
    if (has_osc_message()) {
      msg <- get_osc_message()
      osc_prompt(msg)
    }
  })
  
  observeEvent(osc_prompt(), {
    req(nzchar(osc_prompt()))  # Solo continúa si osc_prompt no está vacío
    prompt(osc_prompt())
    res <- gemini$chat(prompt())
    respuesta(res)
  })
  
  # Mostrar la respuesta en UI
  output$response <- renderText({
    respuesta()
  })
  
  observeEvent(respuesta(), {
    py$enviar(respuesta())
  })
  
  output$oscPrompt <- renderText({
    osc_prompt()  
    })
  
}

# Run the application 
shinyApp(ui = ui, server = server)
