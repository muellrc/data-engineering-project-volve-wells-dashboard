


@requires(extract_data)
class transform_data_wellbores(luigi.Task):
    def run(self):
        # parse EDM XML file
        with self.input().open() as f:
            p = XMLParser(huge_tree=True)
            tree = parse(f, parser=p)
            root = tree.getroot()

        # create list to hold Wellbores
        wellbore_id = []

        # get only actual surveys for valid wellbores
        for child_node in root:
            if child_node.tag == 'CD_DEFINITIVE_SURVEY_HEADER':
                if child_node.attrib['phase'] == 'ACTUAL':
                    wellbore_id.append(child_node.attrib['wellbore_id'])

        # create a list of wellbore legal names for the ids identified based on CD_WELLBORE table in EDM
        wellbore_name = []
        for child_node in root:
            if child_node.tag == 'CD_WELLBORE':
                if child_node.attrib['wellbore_id'] in wellbore_id:
                    wellbore_name.append(
                        child_node.attrib['well_legal_name'].replace('/', '-'))

        # make a dictionary of wellbore ids and names
        id_name_dict = dict(zip(wellbore_id, wellbore_name))

        # write data to luigi output
        wellbores = pd.DataFrame(
            list(id_name_dict.items()), columns=['wellbore_key', 'wellbore_name'])
        list_wellbores = wellbores.values.tolist()

        with self.output().open(mode="w") as f:
            writer = csv.writer(f, delimiter="\t")
            writer.writerows(list_wellbores[1:])

    def output(self):
        return luigi.LocalTarget(self.task_id + ".tsv")


@requires(transform_data_wellbores)
class load_data_wellbores(luigi.Task):

    def run(self):

        with self.input().open() as f:
            # read tsv file holding valid Wellbores
            reader = csv.reader(f,delimiter="\t")
            # create dataframe
            wellbores = pd.DataFrame(
            reader, columns=['wellbore_key', 'wellbore_name'])
            # write to postgres
            engine = create_engine(
                'postgresql://postgres:postgres@dev-postgres-db:5432/postgres')
            wellbores.to_sql(
                'wellbores_clean',
                engine,
                index=False,
                if_exists='replace'
            )

    def output(self):
        return(luigi.contrib.postgres.PostgresTarget('dev-postgres-db', 'postgres', 'postgres', 'postgres', 'wellbores_clean', '1'))

# ==================================END OF WELLBORES==========================================




# ========================================SURVEY DATA========================================


@requires(extract_data)
class transform_data_survey(luigi.Task):
    def run(self):
        # parse EDM XML file
        with self.input().open() as f:
            p = XMLParser(huge_tree=True)
            tree = parse(f, parser=p)
            root = tree.getroot()
        
        survey_data = [
        c.attrib for c in root
        if c.tag == "CD_DEFINITIVE_SURVEY_STATION"
        ]

        with self.output().open(mode="w") as f:
            writer = csv.writer(f, delimiter="\t")
            writer.writerows(survey_data[1:])

    def output(self):
        return luigi.LocalTarget(self.task_id + ".tsv")

@requires(transform_data_survey)
class load_data_survey(luigi.Task):

    def run(self):

        with self.input().open() as f:
            # read tsv file holding valid Wellbores
            reader = csv.reader(f,delimiter="\t")
            # create dataframe
            surveys = pd.DataFrame(
            reader, 
            columns=['well_id', 'wellbore_id', 'def_survey_header_id',
                    'definitive_survey_id', 'azimuth', 'offset_east', 'offset_north',
                    'covariance_yy', 'sequence_no', 'ellipse_vertical', 'covariance_yz',
                    'covariance_zz', 'covariance_xx', 'data_entry_mode', 'covariance_xy',
                    'dogleg_severity', 'inclination', 'covariance_xz', 'ellipse_east',
                    'ellipse_north', 'md', 'casing_radius', 'tvd', 'global_lateral_error'
                    ]
            )

            # write to postgres
            engine = create_engine(
                'postgresql://postgres:postgres@dev-postgres-db:5432/postgres')
            surveys.to_sql(
                'surveys_clean',
                engine,
                index=False,
                if_exists='replace'
            )

    def output(self):
        return(luigi.contrib.postgres.PostgresTarget('dev-postgres-db', 'postgres', 'postgres', 'postgres', 'surveys_clean', '1'))

# ==================================END OF SURVEY DATA==========================================