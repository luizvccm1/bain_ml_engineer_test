# bain_ml_engineer_test
Repositório contendo código para desafio de ML Engineer Senior da Bain Company

1- Criando Pipeline de CI/CD

	1- Entre na sua conta AWS
	2- Busque pelo serviço CloudFormation na janela de busca
	3- Clique em "Criar pilha" e em seguida "com novos recursos"
	4- Na primeira tela clique em "Escolher um modelo existente" e "Fazer upload de um arquivo de modelo"
	5- Clique em "Escolher arquivo" e selecione o arquivo pipeline_stack.yml
	6- Avance para a próxima página
	7- Escolha um nome para a stack do cloudformation a ser criada. Optou-se no exemplo por bain-ml-engineering-test-prd
	8- Escolha um nome para o projeto do sagemaker a ser criado com o pipeline. Optou-se no exemplo por BainMLEngineeringTestPrd
	9- Escolha um Stage para o stack. Optou-se no exemplo por prd.
	10- Proxiga até a última tela do processo
	11- Preencha a caixa dizendo "Entendo que o AWS CloudFormation pode criar recursos do IAM."
	12- Clique em "Enviar"
	
2- Empurrando o repositório para o codecommit 

	1- Crie as chaves para a conexão https com co code commit (para mais detalhes acessar o link https://docs.aws.amazon.com/codecommit/latest/userguide/setting-up-gc.html?icmpid=docs_acc_console_connect_np) 
		1- Buscar o serviço IAM na aba de busca da AWS
		2- Clique em usuários e clique no usuário a sr utilizado para fazer a conexão com o codecommit
		3- Clicar em "Credenciais de segurança" e descer até "Credenciais HTTPS do Git para o AWS CodeCommit"
		4- Clique em "Gerar credenciais"
		5- Salvar o nome de usuário e senha fornecidos localmente
		6- Ir até o code commit e clicar em "Clonar URL" seguido de "Clonar HTTPS"
		6- Ir até o repositório local e executar os seguintes comandos:
			git remote add codecommit <URL Clonada>
			git push codecommit main:prd
		7- Inserir o usuário e senha gerados para a conexão https